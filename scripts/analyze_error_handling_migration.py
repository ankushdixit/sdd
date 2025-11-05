#!/usr/bin/env python3
"""
Analyze codebase for error handling patterns that need migration.

This script identifies all files that use legacy error handling patterns
and need to be migrated to the new standardized exception hierarchy.

Usage:
    python scripts/analyze_error_handling_migration.py

Output:
    - Summary statistics
    - Files grouped by migration complexity
    - Detailed pattern analysis per file
    - Suggested migration order
"""

import ast
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List
from collections import defaultdict


@dataclass
class FileAnalysis:
    """Analysis results for a single file"""
    file_path: str

    # Pattern counts
    return_tuple_count: int = 0
    sys_exit_count: int = 0
    print_error_count: int = 0
    logger_error_count: int = 0
    broad_exception_count: int = 0
    builtin_exception_count: int = 0
    subprocess_calls_count: int = 0

    # Detailed locations
    return_tuple_locations: List[Dict] = None
    sys_exit_locations: List[int] = None
    print_error_locations: List[int] = None
    broad_exception_locations: List[int] = None
    builtin_exception_locations: List[Dict] = None

    # Migration metadata
    complexity_score: int = 0
    uses_new_exceptions: bool = False
    imports_sdd_exceptions: bool = False
    has_tests: bool = False

    def __post_init__(self):
        if self.return_tuple_locations is None:
            self.return_tuple_locations = []
        if self.sys_exit_locations is None:
            self.sys_exit_locations = []
        if self.print_error_locations is None:
            self.print_error_locations = []
        if self.broad_exception_locations is None:
            self.broad_exception_locations = []
        if self.builtin_exception_locations is None:
            self.builtin_exception_locations = []

    def calculate_complexity(self):
        """Calculate migration complexity score (higher = more complex)"""
        self.complexity_score = (
            self.return_tuple_count * 3 +  # Return tuples are most complex
            self.sys_exit_count * 2 +
            self.print_error_count * 1 +
            self.broad_exception_count * 2 +
            self.builtin_exception_count * 1 +
            self.subprocess_calls_count * 1
        )
        return self.complexity_score

    def needs_migration(self) -> bool:
        """Check if file needs migration"""
        return (
            self.return_tuple_count > 0 or
            self.sys_exit_count > 0 or
            self.print_error_count > 0 or
            self.broad_exception_count > 0 or
            self.builtin_exception_count > 0
        )


class ErrorHandlingAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze error handling patterns"""

    def __init__(self, file_path: str, content: str):
        self.file_path = file_path
        self.content = content
        self.lines = content.split('\n')
        self.analysis = FileAnalysis(file_path=file_path)

        # Track current function for return analysis
        self.current_function = None
        self.function_returns = defaultdict(list)

    def visit_Import(self, node):
        """Track imports to detect if file already uses new exceptions"""
        for alias in node.names:
            if 'sdd.core.exceptions' in alias.name:
                self.analysis.imports_sdd_exceptions = True
                self.analysis.uses_new_exceptions = True
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """Track from imports"""
        if node.module and 'sdd.core.exceptions' in node.module:
            self.analysis.imports_sdd_exceptions = True
            self.analysis.uses_new_exceptions = True
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        """Track function definitions for return analysis"""
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)

        # Analyze function returns after visiting
        returns = self.function_returns[node.name]
        if self._looks_like_error_tuple(returns):
            self.analysis.return_tuple_count += 1
            self.analysis.return_tuple_locations.append({
                'function': node.name,
                'line': node.lineno,
                'returns': len(returns)
            })

        self.current_function = old_function

    def visit_Return(self, node):
        """Analyze return statements"""
        if self.current_function and node.value:
            # Check if returning a tuple
            if isinstance(node.value, ast.Tuple):
                self.function_returns[self.current_function].append({
                    'line': node.lineno,
                    'tuple_size': len(node.value.elts),
                    'first_is_bool': self._is_bool_expr(node.value.elts[0])
                })
        self.generic_visit(node)

    def visit_Call(self, node):
        """Analyze function calls"""
        # Check for sys.exit()
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                if node.func.value.id == 'sys' and node.func.attr == 'exit':
                    self.analysis.sys_exit_count += 1
                    self.analysis.sys_exit_locations.append(node.lineno)

        # Check for print() with error messages
        if isinstance(node.func, ast.Name) and node.func.id == 'print':
            if self._looks_like_error_print(node):
                self.analysis.print_error_count += 1
                self.analysis.print_error_locations.append(node.lineno)

        # Check for logger.error/warning calls
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in ('error', 'warning', 'critical'):
                if isinstance(node.func.value, ast.Name) and 'logger' in node.func.value.id.lower():
                    self.analysis.logger_error_count += 1

        # Check for subprocess calls
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                if node.func.value.id == 'subprocess':
                    self.analysis.subprocess_calls_count += 1

        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        """Analyze exception handlers"""
        # Check for broad Exception catching
        if node.type:
            if isinstance(node.type, ast.Name):
                if node.type.id == 'Exception':
                    self.analysis.broad_exception_count += 1
                    self.analysis.broad_exception_locations.append(node.lineno)

        self.generic_visit(node)

    def visit_Raise(self, node):
        """Analyze raise statements"""
        if node.exc:
            if isinstance(node.exc, ast.Call):
                if isinstance(node.exc.func, ast.Name):
                    exc_name = node.exc.func.id
                    # Check for built-in exceptions
                    if exc_name in ('ValueError', 'TypeError', 'RuntimeError', 'OSError', 'IOError'):
                        self.analysis.builtin_exception_count += 1
                        self.analysis.builtin_exception_locations.append({
                            'line': node.lineno,
                            'exception': exc_name
                        })
        self.generic_visit(node)

    def _is_bool_expr(self, node) -> bool:
        """Check if expression is likely a boolean"""
        if isinstance(node, ast.Constant):
            return isinstance(node.value, bool)
        return False

    def _looks_like_error_tuple(self, returns: List[Dict]) -> bool:
        """Check if function returns look like error tuples (bool, str)"""
        if not returns:
            return False

        # Check if any return is a 2-tuple with bool first element
        for ret in returns:
            if ret.get('tuple_size') == 2 and ret.get('first_is_bool'):
                return True

        return False

    def _looks_like_error_print(self, node: ast.Call) -> bool:
        """Check if print statement looks like an error message"""
        # Simple heuristic: check if any arg contains error-related strings
        for arg in node.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                error_keywords = ['error', 'failed', 'fail', 'invalid', 'not found', '❌', '⚠️']
                if any(keyword in arg.value.lower() for keyword in error_keywords):
                    return True
            # Check for f-strings
            if isinstance(arg, ast.JoinedStr):
                return True  # Assume f-strings in print are often errors
        return False


def analyze_file(file_path: Path) -> FileAnalysis:
    """Analyze a single Python file for error handling patterns"""
    try:
        content = file_path.read_text(encoding='utf-8')

        # Parse AST
        tree = ast.parse(content, filename=str(file_path))

        # Run analyzer
        analyzer = ErrorHandlingAnalyzer(str(file_path), content)
        analyzer.visit(tree)

        # Check if test file exists
        test_path = get_test_path(file_path)
        analyzer.analysis.has_tests = test_path.exists() if test_path else False

        # Calculate complexity
        analyzer.analysis.calculate_complexity()

        return analyzer.analysis

    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return FileAnalysis(file_path=str(file_path))


def get_test_path(file_path: Path) -> Path:
    """Get corresponding test file path"""
    # Convert src/sdd/module.py -> tests/unit/test_module.py
    if 'src/sdd' in str(file_path):
        # Find project root by looking for src directory
        parts = file_path.parts
        try:
            src_idx = parts.index('src')
            project_root = Path(*parts[:src_idx])
            # Get path relative to src/sdd/
            sdd_idx = parts.index('sdd')
            relative_parts = parts[sdd_idx + 1:]
            if relative_parts:
                test_name = f"test_{Path(*relative_parts).stem}.py"
                return project_root / 'tests' / 'unit' / test_name
        except (ValueError, IndexError):
            pass
    return None


def analyze_codebase(src_dir: Path) -> Dict[str, FileAnalysis]:
    """Analyze all Python files in src directory"""
    results = {}

    # Skip the new core error handling files
    skip_files = {
        'exceptions.py',
        'error_handlers.py',
        'error_formatter.py'
    }

    for py_file in src_dir.rglob('*.py'):
        if py_file.name in skip_files:
            print(f"Skipping new file: {py_file.name}")
            continue

        if py_file.name.startswith('test_'):
            continue

        if '__pycache__' in str(py_file):
            continue

        print(f"Analyzing: {py_file}")
        analysis = analyze_file(py_file)

        if analysis.needs_migration():
            results[str(py_file)] = analysis

    return results


def generate_report(analyses: Dict[str, FileAnalysis]) -> dict:
    """Generate migration report"""
    report = {
        'summary': {
            'total_files_analyzed': len(analyses),
            'files_needing_migration': sum(1 for a in analyses.values() if a.needs_migration()),
            'total_return_tuples': sum(a.return_tuple_count for a in analyses.values()),
            'total_sys_exits': sum(a.sys_exit_count for a in analyses.values()),
            'total_print_errors': sum(a.print_error_count for a in analyses.values()),
            'total_broad_exceptions': sum(a.broad_exception_count for a in analyses.values()),
            'total_builtin_exceptions': sum(a.builtin_exception_count for a in analyses.values()),
        },
        'files_by_complexity': {},
        'files_by_module': defaultdict(list),
        'migration_groups': {
            'simple': [],    # 1-5 points
            'medium': [],    # 6-15 points
            'complex': [],   # 16+ points
        }
    }

    # Sort by complexity
    sorted_analyses = sorted(analyses.values(), key=lambda a: a.complexity_score, reverse=True)

    for analysis in sorted_analyses:
        file_path = Path(analysis.file_path)

        # Extract module name
        if 'src/sdd' in str(file_path):
            parts = file_path.parts
            sdd_idx = parts.index('sdd')
            module = parts[sdd_idx + 1] if len(parts) > sdd_idx + 1 else 'core'
            report['files_by_module'][module].append(analysis.file_path)

        # Categorize by complexity
        if analysis.complexity_score <= 5:
            report['migration_groups']['simple'].append(analysis.file_path)
        elif analysis.complexity_score <= 15:
            report['migration_groups']['medium'].append(analysis.file_path)
        else:
            report['migration_groups']['complex'].append(analysis.file_path)

        report['files_by_complexity'][analysis.file_path] = {
            'score': analysis.complexity_score,
            'patterns': {
                'return_tuples': analysis.return_tuple_count,
                'sys_exits': analysis.sys_exit_count,
                'print_errors': analysis.print_error_count,
                'broad_exceptions': analysis.broad_exception_count,
                'builtin_exceptions': analysis.builtin_exception_count,
            },
            'has_tests': analysis.has_tests,
            'uses_new_exceptions': analysis.uses_new_exceptions
        }

    return report


def print_summary_report(report: dict, analyses: Dict[str, FileAnalysis]):
    """Print human-readable summary"""
    print("\n" + "="*80)
    print("ERROR HANDLING MIGRATION ANALYSIS")
    print("="*80)

    print("\n📊 SUMMARY")
    print(f"  Files analyzed: {report['summary']['total_files_analyzed']}")
    print(f"  Files needing migration: {report['summary']['files_needing_migration']}")
    print(f"\n  Pattern counts:")
    print(f"    Return tuples (bool, str): {report['summary']['total_return_tuples']}")
    print(f"    sys.exit() calls: {report['summary']['total_sys_exits']}")
    print(f"    print() errors: {report['summary']['total_print_errors']}")
    print(f"    Broad Exception catches: {report['summary']['total_broad_exceptions']}")
    print(f"    Built-in exceptions: {report['summary']['total_builtin_exceptions']}")

    print("\n📋 MIGRATION GROUPS")
    print(f"  Simple (1-5 points): {len(report['migration_groups']['simple'])} files")
    print(f"  Medium (6-15 points): {len(report['migration_groups']['medium'])} files")
    print(f"  Complex (16+ points): {len(report['migration_groups']['complex'])} files")

    print("\n🔝 TOP 10 MOST COMPLEX FILES")
    sorted_by_complexity = sorted(
        analyses.values(),
        key=lambda a: a.complexity_score,
        reverse=True
    )[:10]

    for i, analysis in enumerate(sorted_by_complexity, 1):
        file_name = Path(analysis.file_path).name
        print(f"  {i:2d}. {file_name:30s} (score: {analysis.complexity_score:2d}) "
              f"RT:{analysis.return_tuple_count} "
              f"SE:{analysis.sys_exit_count} "
              f"PE:{analysis.print_error_count} "
              f"BE:{analysis.broad_exception_count} "
              f"BX:{analysis.builtin_exception_count}")

    print("\n📁 FILES BY MODULE")
    for module, files in sorted(report['files_by_module'].items()):
        print(f"  {module:20s}: {len(files)} files")

    print("\n💡 SUGGESTED PARALLEL MIGRATION GROUPS")
    print("  The following groups can be migrated in parallel:")

    # Group by module for parallel processing
    module_groups = defaultdict(list)
    for file_path, data in report['files_by_complexity'].items():
        if 'src/sdd' in file_path:
            parts = Path(file_path).parts
            sdd_idx = parts.index('sdd')
            module = parts[sdd_idx + 1] if len(parts) > sdd_idx + 1 else 'core'
            module_groups[module].append((file_path, data['score']))

    for i, (module, files) in enumerate(sorted(module_groups.items()), 1):
        print(f"\n  Group {i} - {module.upper()} MODULE ({len(files)} files)")
        sorted_files = sorted(files, key=lambda x: x[1], reverse=True)
        for file_path, score in sorted_files[:5]:  # Show top 5
            file_name = Path(file_path).name
            print(f"    - {file_name:30s} (complexity: {score})")
        if len(files) > 5:
            print(f"    ... and {len(files) - 5} more files")

    print("\n" + "="*80)


def save_detailed_report(report: dict, analyses: Dict[str, FileAnalysis], output_file: Path):
    """Save detailed JSON report"""
    detailed = {
        'summary': report['summary'],
        'migration_groups': report['migration_groups'],
        'files': {}
    }

    for file_path, analysis in analyses.items():
        detailed['files'][file_path] = {
            'complexity_score': analysis.complexity_score,
            'needs_migration': analysis.needs_migration(),
            'has_tests': analysis.has_tests,
            'uses_new_exceptions': analysis.uses_new_exceptions,
            'patterns': {
                'return_tuples': {
                    'count': analysis.return_tuple_count,
                    'locations': analysis.return_tuple_locations
                },
                'sys_exits': {
                    'count': analysis.sys_exit_count,
                    'locations': analysis.sys_exit_locations
                },
                'print_errors': {
                    'count': analysis.print_error_count,
                    'locations': analysis.print_error_locations
                },
                'broad_exceptions': {
                    'count': analysis.broad_exception_count,
                    'locations': analysis.broad_exception_locations
                },
                'builtin_exceptions': {
                    'count': analysis.builtin_exception_count,
                    'locations': analysis.builtin_exception_locations
                }
            }
        }

    output_file.write_text(json.dumps(detailed, indent=2))
    print(f"\n✅ Detailed report saved to: {output_file}")


def main():
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    src_dir = project_root / 'src' / 'sdd'

    if not src_dir.exists():
        print(f"❌ Source directory not found: {src_dir}")
        return 1

    print(f"🔍 Analyzing codebase at: {src_dir}")

    # Analyze all files
    analyses = analyze_codebase(src_dir)

    # Generate report
    report = generate_report(analyses)

    # Print summary
    print_summary_report(report, analyses)

    # Save detailed report
    output_file = project_root / 'error_handling_migration_analysis.json'
    save_detailed_report(report, analyses, output_file)

    return 0


if __name__ == '__main__':
    exit(main())
