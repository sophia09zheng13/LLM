"""Tools: write one or more files to disk and commit them to git."""

import git
import os
import subprocess
import tempfile

from tools.doctests import doctests
from tools.utils import is_path_safe


tool_schema = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": (
            "Write or update a single file and commit it to git. "
            "Provide 'contents' to overwrite the whole file, or 'diff' "
            "(unified diff) to patch an existing file."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file.",
                },
                "contents": {
                    "type": "string",
                    "description": "Full file contents (for new files or complete rewrites).",
                },
                "diff": {
                    "type": "string",
                    "description": "Unified diff to apply to an existing file (for partial updates).",
                },
                "commit_message": {
                    "type": "string",
                    "description": "Git commit message.",
                },
            },
            "required": ["path", "commit_message"],
        },
    },
}

write_files_schema = {
    "type": "function",
    "function": {
        "name": "write_files",
        "description": "Write or update multiple files and commit them to git in one commit.",
        "parameters": {
            "type": "object",
            "properties": {
                "files": {
                    "type": "array",
                    "description": "List of files to write or update.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "contents": {"type": "string"},
                            "diff": {"type": "string"},
                        },
                        "required": ["path"],
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


def _apply_diff(path, diff):
    """Apply a unified diff to *path* using wiggle, which tolerates
    fuzzy/misaligned line numbers that LLMs typically generate.

    wiggle usage: wiggle --merge --replace original patch.diff
    Returns None on success, or an error string.

    >>> import git as _git
    >>> repo = _git.Repo('.')
    >>> with open('tmp_wiggle_test.txt', 'w') as fh: _ = fh.write('hello\\nworld\\n')
    >>> _ = repo.index.add(['tmp_wiggle_test.txt'])
    >>> _ = repo.index.commit('[docchat] add tmp_wiggle_test.txt')
    >>> diff = '--- a/tmp_wiggle_test.txt\\n+++ b/tmp_wiggle_test.txt\\n@@ -1,2 +1,2 @@\\n hello\\n-world\\n+earth\\n'
    >>> _apply_diff('tmp_wiggle_test.txt', diff) is None
    True
    >>> open('tmp_wiggle_test.txt').read()
    'hello\\nearth\\n'
    >>> _ = repo.git.rm('-f', 'tmp_wiggle_test.txt')
    >>> _ = repo.index.commit('[docchat] cleanup tmp_wiggle_test.txt')
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.diff', delete=False, encoding='utf-8') as f:
        f.write(diff)
        diff_path = f.name
    try:
        result = subprocess.run(
            ['wiggle', '--merge', '--replace', path, diff_path],
            capture_output=True, text=True,
        )
        # wiggle saves a .porig backup — remove it
        porig = path + '.porig'
        if os.path.exists(porig):
            os.unlink(porig)
        if result.returncode > 1:
            return f"Error applying diff to '{path}': {result.stderr or result.stdout}"
        return None
    finally:
        os.unlink(diff_path)


def write_files(files, commit_message):
    """Write or update each file in *files* and commit with *commit_message*.

    Each item must have 'path' and either 'contents' (full file) or 'diff'
    (unified diff applied via wiggle).  Returns doctest output for any .py
    files, otherwise a confirmation message.

    >>> import git as _git
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
    >>> write_files([{'path': 'tmp_bad.txt'}], 'bad')
    "Error: must provide 'contents' or 'diff' for 'tmp_bad.txt'"
    """
    for f in files:
        if not is_path_safe(f['path']):
            return f"Error: path '{f['path']}' is not allowed"
        if 'contents' not in f and 'diff' not in f:
            return f"Error: must provide 'contents' or 'diff' for '{f['path']}'"

    for f in files:
        if 'diff' in f:
            err = _apply_diff(f['path'], f['diff'])
            if err:
                return err
        else:
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


def write_file(path, contents=None, commit_message=None, diff=None):
    """Write or update a single file. Thin wrapper around write_files.

    >>> write_file('/etc/passwd', contents='x', commit_message='bad') == "Error: path '/etc/passwd' is not allowed"
    True
    """
    f = {'path': path}
    if contents is not None:
        f['contents'] = contents
    if diff is not None:
        f['diff'] = diff
    return write_files([f], commit_message)
