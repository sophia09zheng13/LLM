"""Tool: run doctests on a Python file and return the output."""

import subprocess

from tools.utils import is_path_safe


tool_schema = {
    "type": "function",
    "function": {
        "name": "doctests",
        "description": "Run doctests on a Python file and return the verbose output.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the Python file to test.",
                },
            },
            "required": ["path"],
        },
    },
}


def doctests(path):
    """Run doctests on *path* and return the combined stdout+stderr output.

    >>> doctests('/etc/passwd')
    "Error: path '/etc/passwd' is not allowed"
    >>> doctests('../secret.py')
    "Error: path '../secret.py' is not allowed"
    >>> 'Test passed' in doctests('tools/calculate.py')
    True
    """
    if not is_path_safe(path):
        return f"Error: path '{path}' is not allowed"
    result = subprocess.run(
        ['python', '-m', 'doctest', path, '-v'],
        capture_output=True, text=True,
    )
    return result.stdout + result.stderr
