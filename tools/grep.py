"""Tool: search for lines matching a regex across files that match a glob."""

import glob
import os
import re

from tools.utils import is_path_safe


tool_schema = {
    "type": "function",
    "function": {
        "name": "grep",
        "description": "Search for lines matching a regex pattern across files matching a glob path.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "The regex pattern to search for",
                },
                "path": {
                    "type": "string",
                    "description": "A file path, optionally with globs (e.g. 'tools/*.py')",
                },
            },
            "required": ["pattern", "path"],
        },
    },
}


def grep(pattern, path):
    """Search every file matched by *path* (a glob) for lines matching *pattern*.

    Returns all matching lines as ``filepath:line`` pairs joined by newlines.
    Returns an empty string when there are no matches.
    Blocks absolute paths and directory traversal.

    # these are good tests
    
    >>> grep('^def grep', 'tools/grep.py')
    'tools/grep.py:def grep(pattern, path):'
    >>> grep('zzz_no_match', 'tools/calculate.py')
    ''
    >>> grep('^def ', 'tools/*.py')
    'tools/calculate.py:def calculate(expression):\\ntools/cat.py:def cat(file):\\ntools/grep.py:def grep(pattern, path):\\ntools/ls.py:def ls(folder=None):\\ntools/utils.py:def is_path_safe(path):'
    >>> grep('^def ', '/etc/passwd')
    "Error: path '/etc/passwd' is not allowed"
    >>> grep('^def ', '../secret.py')
    "Error: path '../secret.py' is not allowed"
    >>> grep('anything', 'tools')  # tools is a directory, not a file — yields no matches
    ''
    >>> import unittest.mock
    >>> with unittest.mock.patch('builtins.open', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'bad')):
    ...     grep('^def', 'tools/ls.py')  # binary file — silently skipped
    ''
    """
    if not is_path_safe(path):
        return f"Error: path '{path}' is not allowed"

    output_lines = []
    for filepath in sorted(glob.glob(path)):
        if os.path.isdir(filepath):
            continue
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if re.search(pattern, line):
                        output_lines.append(f"{filepath}:{line.rstrip()}")
        except (UnicodeDecodeError, FileNotFoundError):
            continue

    return '\n'.join(output_lines)
