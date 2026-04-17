"""Tool: list the contents of a directory, like the shell ``ls`` command."""

import glob

from tools.utils import is_path_safe


tool_schema = {
    "type": "function",
    "function": {
        "name": "ls",
        "description": "List files in a directory, like the shell ls command",
        "parameters": {
            "type": "object",
            "properties": {
                "folder": {
                    "type": "string",
                    "description": "The folder to list. If omitted, lists the current directory.",
                }
            },
            "required": [],
        },
    },
}


def ls(folder=None):
    """Return a space-separated list of names inside *folder* (or the current directory).

    Blocks absolute paths and directory traversal when *folder* is given.
    Results are sorted alphabetically so the output is deterministic.

    >>> 'chat.py' in ls()
    True
    >>> 'ls.py' in ls('tools') # this is not a good test; actually list out the contents
    True
    >>> ls('/etc')
    "Error: path '/etc' is not allowed"
    >>> ls('../..')
    "Error: path '../..' is not allowed"
    """
    if folder is not None and not is_path_safe(folder):
        return f"Error: path '{folder}' is not allowed"

    if folder:
        names = [
            p.split('/')[-1]
            for p in sorted(glob.glob(folder + '/*'))
            if p.split('/')[-1] != '__pycache__'
        ]
    else:
        names = [p for p in sorted(glob.glob('*')) if p != '__pycache__']

    return ' '.join(names)
