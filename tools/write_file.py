"""Tools: write one or more files to disk and commit them to git."""

import git

from tools.doctests import doctests
from tools.utils import is_path_safe


tool_schema = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "Write a single file and commit it to git.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to write.",
                },
                "contents": {
                    "type": "string",
                    "description": "Contents to write to the file.",
                },
                "commit_message": {
                    "type": "string",
                    "description": "Git commit message.",
                },
            },
            "required": ["path", "contents", "commit_message"],
        },
    },
}

write_files_schema = {
    "type": "function",
    "function": {
        "name": "write_files",
        "description": "Write multiple files and commit them to git in one commit.",
        "parameters": {
            "type": "object",
            "properties": {
                "files": {
                    "type": "array",
                    "description": "List of files to write.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "contents": {"type": "string"},
                        },
                        "required": ["path", "contents"],
                    },
                },
                "commit_message": {
                    "type": "string",
                    "description": "Git commit message.",
                },
            },
            "required": ["files", "commit_message"],
        },
    },
}


def write_files(files, commit_message):
    """Write each file in *files* and commit them all with *commit_message*.

    Each item in *files* must have ``path`` and ``contents`` keys.
    Returns doctest output for any ``.py`` files written, otherwise a
    confirmation message.

    >>> import os, git as _git
    >>> repo = _git.Repo('.')
    >>> result = write_files([{'path': 'tmp_test_write.txt', 'contents': 'hello'}], 'test write')
    >>> 'tmp_test_write.txt' in result
    True
    >>> _ = repo.git.rm('tmp_test_write.txt')
    >>> _ = repo.index.commit('[docchat] cleanup test file')
    >>> result2 = write_files([{'path': 'tmp_test_write.py', 'contents': '# no doctests'}], 'test py write')
    >>> isinstance(result2, str)
    True
    >>> _ = repo.git.rm('tmp_test_write.py')
    >>> _ = repo.index.commit('[docchat] cleanup py test file')
    """
    for f in files:
        if not is_path_safe(f['path']):
            return f"Error: path '{f['path']}' is not allowed"

    for f in files:
        with open(f['path'], 'w', encoding='utf-8') as fp:
            fp.write(f['contents'])

    repo = git.Repo('.')
    paths = [f['path'] for f in files]
    repo.index.add(paths)
    repo.index.commit(f'[docchat] {commit_message}')

    py_outputs = [doctests(p) for p in paths if p.endswith('.py')]
    if py_outputs:
        return '\n'.join(py_outputs)
    return f"Wrote and committed: {', '.join(paths)}"


def write_file(path, contents, commit_message):
    """Write a single file and commit it. Thin wrapper around write_files.

    >>> write_file('/etc/passwd', 'x', 'bad') == "Error: path '/etc/passwd' is not allowed"
    True
    """
    return write_files([{'path': path, 'contents': contents}], commit_message)
