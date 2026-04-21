# Sophia's Personal LLM

[![tests](https://github.com/sophia09zheng13/LLM/actions/workflows/tests.yml/badge.svg)](https://github.com/sophia09zheng13/LLM/actions/workflows/tests.yml)
[![integration-tests](https://github.com/sophia09zheng13/LLM/actions/workflows/integration-tests.yml/badge.svg)](https://github.com/sophia09zheng13/LLM/actions/workflows/integration-tests.yml)
[![PyPI](https://img.shields.io/pypi/v/cmc-csci040-sophiazheng)](https://pypi.org/project/cmc-csci040-sophiazheng/)
[![flake8](https://github.com/sophia09zheng13/LLM/actions/workflows/flake8.yml/badge.svg)](https://github.com/sophia09zheng13/LLM/actions/workflows/flake8.yml)
[![codecov](https://codecov.io/gh/sophia09zheng13/LLM/branch/main/graph/badge.svg)](https://codecov.io/gh/sophia09zheng13/LLM)

A pirate-themed command-line chat agent powered by Groq's LLM API. The agent
can answer questions, remember conversational context, and call built-in tools
(`calculate`, `cat`, `grep`, `ls`, `write_file`, `write_files`, `doctests`, `rm`,
`pip_install`) either automatically or via `/slash` commands.

The agent automatically commits every file change to git, so all edits are
reversible.

![demo](demo.gif)


## Installation

Install the package from PyPI:

```
$ pip install cmc-csci040-sophiazheng
```

Set your Groq API key so the agent can reach the LLM:

```
$ export GROQ_API_KEY=your_key_here
```

## Usage

The agent remembers information across messages in the same session, so you can refer back to things you said earlier:

```
$chat
chat> my name is Alice
Arrr, pleasure to meet ye, Alice!
chat> what is my name?
Yer name be Alice, savvy?
```

### Slash commands (tool call without LLM round-trip)

Prefix any tool name with `/` to run it directly and add the result to context.

Running `/ls` first lets the model answer follow-up questions about the directory instantly, without making a second API call.

```
chat> /ls tools
__init__.py calculate.py cat.py grep.py ls.py utils.py
chat> what files are in the tools folder?
There be six files in the tools folder, matey.
```

Using `/calculate` guarantees exact arithmetic results because it evaluates the expression in Python rather than relying on the model to do mental math.

```
chat> /calculate 99 * 99
{"result": 9801}
```

Using `/grep` lets you search your codebase with a regex and feed the matches directly into the conversation so the model can reason about the results.

```
chat> /grep ^def tools/*.py
tools/calculate.py:def calculate(expression):
tools/cat.py:def cat(file):
tools/grep.py:def grep(pattern, path):
tools/ls.py:def ls(folder=None):
tools/utils.py:def is_path_safe(path):
```

Using `/cat` returns the raw file contents without any pirate rephrasing, so you always see the exact text of the file.

```
chat> /cat tools/calculate.py
"""Tool: evaluate a mathematical expression and return the result as JSON."""
...
```

Using `/compact` summarizes the entire conversation so far into 1-5 lines and replaces the message history with that summary. This keeps token counts low for long sessions.

```
chat> my name is Alice
Arrr, pleasure to meet ye, Alice!
chat> what is 2+2?
Arrr, it be 4, matey!
chat> /compact
Alice introduced herself. The assistant confirmed her name and answered that 2+2 equals 4.
```

## Agent in action

Ask the agent to create a file and it will write it and commit it automatically:

```
chat> write a file called hello.txt that says "Ahoy, world!"
Arrr, I've written yer file and committed it to git, matey!

$ git log --oneline -3
a1b2c3d [docchat] add hello.txt
...
```

Ask the agent to write a Python file and it will run doctests automatically:

```
chat> write a python file called greet.py with a function greet(name) that returns "Hello, " + name, with a doctest
Arrr, the file be written and all doctests pass, matey!
```

Ask the agent to delete a file and the removal is committed to git:

```
chat> delete hello.txt
Arrr, hello.txt has walked the plank and the deed be committed!

$ git log --oneline -3
d4e5f6a [docchat] rm hello.txt
a1b2c3d [docchat] add hello.txt
...
```

Ask the agent to patch a file instead of rewriting it:

```
chat> add a docstring to the greet function in greet.py
Arrr, I've patched the file and committed the change, matey!
```

Ask the agent to install a package:

```
chat> install the requests library
Arrr, requests be installed and ready to sail!
```

## Extra credit features

### pip_install tool

The agent can install Python packages with `pip_install`. This lets it pull in
libraries it needs to complete a task without leaving the chat session.

**Warning:** PyPI packages run arbitrary code on your machine. Only ask the
agent to install packages you trust.

### Ralph Wiggum loop

Whenever the agent writes a Python file and the doctests fail, it is
automatically forced into another round of tool use to fix the code. It cannot
give a final response until all doctests pass. This means you can ask the agent
to "write a function with doctests" and it will keep trying until the tests are
green.

### Diff/patch via wiggle

`write_file` and `write_files` now accept a `diff` parameter (unified diff
format) in addition to `contents`. Instead of rewriting the whole file, the
agent can send just the changed lines. The diff is applied using
[wiggle](https://github.com/neilbrown/wiggle), which tolerates the fuzzy
line numbers that LLMs typically produce.

This saves tokens for large files and reduces the chance of the model
accidentally introducing typos in unchanged code.

Requires wiggle: `brew install wiggle` (macOS) or `sudo apt install wiggle` (Linux).

## Tools

| Tool | Description |
|------|-------------|
| `calculate` | Evaluate a Python arithmetic expression |
| `ls [folder]` | List files in a directory |
| `cat file` | Print the contents of a file |
| `grep pattern path` | Search for lines matching a regex across files |
| `write_file path [contents\|diff] msg` | Write or patch a file and commit it |
| `write_files files msg` | Write or patch multiple files in one git commit |
| `doctests path` | Run doctests on a Python file and return the output |
| `rm path` | Delete files matching a glob and commit the removal |
| `pip_install library` | Install a Python package via pip |
| `compact` | Summarize conversation history and reset to a compact summary (slash command only) |
