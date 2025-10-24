# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.5.x   | :white_check_mark: |
| < 0.5   | :x:                |

## Reporting a Vulnerability

We take the security of SDD seriously. If you discover a security vulnerability, please follow these steps:

### 1. **Do Not** Open a Public Issue

Security vulnerabilities should not be disclosed publicly until a fix is available.

### 2. Report Privately

Please report security vulnerabilities by emailing the maintainer or using GitHub's private vulnerability reporting feature:

- **GitHub Private Reporting:** Go to the [Security tab](https://github.com/ankushdixit/sdd/security/advisories/new) and click "Report a vulnerability"
- **Email:** Create a new issue with the tag `[SECURITY]` and we'll handle it privately

### 3. Include Details

When reporting a vulnerability, please include:

- **Description:** Clear description of the vulnerability
- **Impact:** What could an attacker potentially do?
- **Reproduction Steps:** How to reproduce the issue
- **Affected Versions:** Which versions are affected
- **Suggested Fix:** If you have ideas for how to fix it

### 4. Response Timeline

- **Initial Response:** Within 48 hours
- **Status Update:** Within 7 days with assessment
- **Fix Timeline:** Depends on severity
  - Critical: Within 7 days
  - High: Within 14 days
  - Medium: Within 30 days
  - Low: Next regular release

## Security Considerations for Users

### Quality Gates

SDD includes security scanning via quality gates:
- **bandit** - Python security linting
- **safety** - Dependency vulnerability scanning
- **npm audit** - JavaScript/TypeScript security

Enable these in `.session/config.json`:

```json
{
  "quality_gates": {
    "security": {
      "enabled": true,
      "required": true,
      "fail_on": "high"
    }
  }
}
```

### Safe Practices

When using SDD:

1. **Review Generated Commands:** Always review git commands before execution
2. **Protect Secrets:** Never commit sensitive data (API keys, passwords, tokens)
3. **Keep Dependencies Updated:** Run `pip install --upgrade` regularly for Python dependencies
4. **Review PRs:** Even automated PRs should be reviewed before merging
5. **Use .gitignore:** Ensure sensitive files are excluded from version control

### Data Storage

SDD stores data locally in your project:
- `.session/` directory contains project state
- No data is transmitted to external servers
- All operations are local to your machine

### Permissions

SDD requires:
- **Read/Write:** Project files and `.session/` directory
- **Git Operations:** Commit, push, branch management
- **Shell Execution:** Running quality gate tools (pytest, ruff, etc.)

Review the scripts in `scripts/` directory to understand what operations are performed.

## Security Updates

Security updates will be announced via:
- GitHub Security Advisories
- Release notes with `[SECURITY]` tag
- Repository README (for critical issues)

## Scope

### In Scope

- Vulnerabilities in SDD's Python scripts
- Security issues in command execution
- Git workflow security concerns
- Data leakage risks
- Dependency vulnerabilities

### Out of Scope

- Claude Code application itself (report to Anthropic)
- Third-party tools (pytest, ruff, etc.) - report to respective projects
- Git itself - report to Git project
- User's own code and configurations

## Acknowledgments

We appreciate security researchers and users who responsibly disclose vulnerabilities. Contributors will be acknowledged (with permission) in:
- Security advisory
- Release notes
- Project credits

Thank you for helping keep SDD and its users safe!
