"""Tool: install a Python package via pip.

WARNING: PyPI packages can contain arbitrary code. Only install packages you trust.
"""

import subprocess


tool_schema = {
    "type": "function",
    "function": {
        "name": "pip_install",
        "description": (
            "Install a Python package using pip. "
            "WARNING: only install trusted packages — PyPI code runs on your machine."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "library_name": {
                    "type": "string",
                    "description": "The name of the package to install.",
                },
            },
            "required": ["library_name"],
        },
    },
}


def pip_install(library_name):
    """Install *library_name* using pip and return the combined output.

    >>> result = pip_install('pip')
    >>> 'already satisfied' in result.lower() or 'Successfully installed' in result
    True
    """
    result = subprocess.run(
        ['pip3', 'install', library_name],
        capture_output=True, text=True,
    )
    return result.stdout + result.stderr
