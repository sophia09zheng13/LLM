"""Tool: delete files matching a glob and commit the removal to git."""

import glob
import os

import git

from tools.utils import is_path_safe


tool_schema = {
    "type": "function",
    "function": {
        "name": "rm",
        "description": "Delete files matching a path (supports globs) and commit the removal.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path or glob pattern to delete.",
                },
            },
            "required": ["path"],
        },
    },
}


def rm(path):
    """Delete all files matching *path* (a glob) and commit the removal.

    >>> rm('/etc/passwd')
    "Error: path '/etc/passwd' is not allowed"
    >>> rm('../secret.py')
    "Error: path '../secret.py' is not allowed"
    >>> rm('nonexistent_zzz_*.txt')
    "Error: no files found matching 'nonexistent_zzz_*.txt'"
    >>> import git as _git
    >>> repo = _git.Repo('.')
    >>> with open('tmp_rm_test.txt', 'w') as f: _ = f.write('x')
    >>> _ = repo.index.add(['tmp_rm_test.txt'])
    >>> _ = repo.index.commit('[docchat] add tmp file for rm test')
    >>> rm('tmp_rm_test.txt')
    'Removed: tmp_rm_test.txt'
    """
    if not is_path_safe(path):
        return f"Error: path '{path}' is not allowed"

    files = sorted(glob.glob(path))
    if not files:
        return f"Error: no files found matching '{path}'"

    for f in files:
        os.remove(f)

    repo = git.Repo('.')
    repo.index.remove(files)
    repo.index.commit(f'[docchat] rm {path}')

    return f"Removed: {', '.join(files)}"
