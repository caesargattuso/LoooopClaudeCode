#!/usr/bin/env python3
"""Logger Module - Global logger with file logging and console task output"""
import os
import sys
from datetime import datetime

# Global logger instance
_logger = None


def init_logger(looop_dir: str):
    """Initialize global logger"""
    global _logger
    _logger = Logger(looop_dir)
    return _logger


def get_logger():
    """Get global logger instance"""
    global _logger
    if _logger is None:
        raise RuntimeError("Logger not initialized. Call init_logger() first.")
    return _logger


def close_logger():
    """Close global logger"""
    global _logger
    if _logger:
        _logger.close()
        _logger = None


class Logger:
    """Logger with file logging (detailed) and console output (task status)"""

    def __init__(self, looop_dir: str):
        """Initialize logger with .looop directory path"""
        self.looop_dir = looop_dir
        os.makedirs(looop_dir, exist_ok=True)

        # Log file: YYYY-MM-DD.log
        today = datetime.now().strftime('%Y-%m-%d')
        self.log_file = os.path.join(looop_dir, f"{today}.log")

        # Open log file for appending
        self._file = open(self.log_file, 'a', encoding='utf-8')

        # Session start
        self._log_file('INFO', 'Session started')

    def close(self):
        """Close log file"""
        self._log_file('INFO', 'Session ended')
        self._file.close()

    def _log_file(self, level: str, msg: str):
        """Write to log file with timestamp (second precision)"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self._file.write(f"{timestamp} [{level}] {msg}\n")
        self._file.flush()

    def _color(self, text: str, code: str) -> str:
        """Apply ANSI color"""
        return f"\033[{code}{text}\033[0m"

    # === Console Output (Task Status) ===

    def task_start(self, task_id: int, task_name: str, priority: str):
        """Console: task started"""
        time = datetime.now().strftime('%H:%M:%S')
        print(f"{time} [{self._color('START', '36m')}] Task #{task_id}: {task_name} (priority: {priority})")
        self._log_file('INFO', f"Task #{task_id}: {task_name} - Started")

    def task_end(self, task_id: int, task_name: str, status: str):
        """Console: task ended"""
        time = datetime.now().strftime('%H:%M:%S')
        if status == "completed":
            status_text = self._color('DONE', '32m')
        else:
            status_text = self._color('MANUAL', '33m')
        print(f"{time} [{status_text}] Task #{task_id}: {task_name}")
        self._log_file('INFO', f"Task #{task_id}: {task_name} - {status}")

    def progress(self, current: int, total: int, task_name: str = None):
        """Console: show progress bar"""
        if total == 0:
            percent = 0
            filled = 0
        else:
            percent = int(current / total * 100)
            filled = min(20, int(percent / 5))

        bar = '=' * filled + '>' + ' ' * (20 - filled - 1)
        line = f"[{bar}] {current}/{total} ({percent}%)"

        if task_name:
            display = task_name[:25] + "..." if len(task_name) > 25 else task_name
            line += f" {display}"

        print(line)
        self._log_file('DEBUG', f"Progress: {current}/{total} ({percent}%)")

    def info(self, msg: str):
        """Console + file: info message"""
        time = datetime.now().strftime('%H:%M:%S')
        print(f"{time} [{self._color('INFO', '32m')}] {msg}")
        self._log_file('INFO', msg)

    def warning(self, msg: str):
        """Console + file: warning message"""
        time = datetime.now().strftime('%H:%M:%S')
        print(f"{time} [{self._color('WARN', '33m')}] {msg}")
        self._log_file('WARNING', msg)

    def error(self, msg: str):
        """Console + file: error message"""
        time = datetime.now().strftime('%H:%M:%S')
        print(f"{time} [{self._color('ERROR', '31m')}] {msg}")
        self._log_file('ERROR', msg)

    def separator(self, char: str = "=", length: int = 60):
        """Console: separator line"""
        print(char * length)

    def blank(self):
        """Console: blank line"""
        print()

    # === File Logging Only (Detailed) ===

    def debug(self, msg: str):
        """File only: debug message"""
        self._log_file('DEBUG', msg)

    def claude(self, line: str):
        """File only: Claude CLI output"""
        self._log_file('CLAUDE', line.rstrip('\n\r'))