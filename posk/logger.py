"""
posk/logger.py
==============
MODULE 8 — Execution Logger
Writes a structured, timestamped execution log to logs/execution_log.txt.

This satisfies Phase 3 Section 2 requirement:
  "Execution Logs proving components function together"

Every log entry is also printed to stdout (terminal output = log mirror).
"""

import os
import time


class Logger:
    """
    Simple append-mode logger that mirrors all output to a log file.
    """

    def __init__(self, log_dir="logs", filename="execution_log.txt"):
        os.makedirs(log_dir, exist_ok=True)
        self.path = os.path.join(log_dir, filename)
        self._file = open(self.path, "w", encoding="utf-8")
        self._write_header()

    def _write_header(self):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        self._file.write(f"PoSk Phase 3 — Execution Log\n")
        self._file.write(f"Generated: {ts}\n")
        self._file.write(f"{'='*64}\n\n")
        self._file.flush()

    def write_line(self, line):
        """Write a single line to the log file (stdout handled by caller)."""
        self._file.write(line + "\n")
        self._file.flush()

    def section(self, title):
        """Write a visual section separator."""
        sep = f"\n{'─'*64}\n  {title}\n{'─'*64}"
        print(sep)
        self.write_line(sep)

    def close(self):
        self._file.close()