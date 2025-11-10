#!/usr/bin/env python3
"""
JSON reporter for quality gate results.
"""

from __future__ import annotations

import json
from typing import Any

from solokit.quality.reporters.base import Reporter


class JSONReporter(Reporter):
    """Generates JSON-formatted reports."""

    def __init__(self, indent: int = 2):
        """Initialize the JSON reporter.

        Args:
            indent: Number of spaces for JSON indentation (default: 2)
        """
        self.indent = indent

    def generate(self, aggregated_results: dict[str, Any]) -> str:
        """Generate a JSON report.

        Args:
            aggregated_results: Aggregated results from ResultAggregator

        Returns:
            JSON-formatted report string
        """
        return json.dumps(aggregated_results, indent=self.indent)
