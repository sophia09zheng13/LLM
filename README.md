# Sophia's Personal LLM

[![tests](https://github.com/sophia09zheng13/LLM/actions/workflows/tests.yml/badge.svg)](https://github.com/sophia09zheng13/LLM/actions/workflows/tests.yml)
[![integration-tests](https://github.com/sophia09zheng13/LLM/actions/workflows/integration-tests.yml/badge.svg)](https://github.com/sophia09zheng13/LLM/actions/workflows/integration-tests.yml)
[![PyPI](https://img.shields.io/pypi/v/cmc-csci040-sophiazheng)](https://pypi.org/project/cmc-csci040-sophiazheng/)
[![flake8](https://github.com/sophia09zheng13/LLM/actions/workflows/flake8.yml/badge.svg)](https://github.com/sophia09zheng13/LLM/actions/workflows/flake8.yml)
[![codecov](https://codecov.io/gh/sophia09zheng13/LLM/branch/main/graph/badge.svg)](https://codecov.io/gh/sophia09zheng13/LLM)

A pirate-themed command-line chat agent powered by Groq's LLM API. The agent
can answer questions, remember conversational context, and call built-in tools
(`calculate`, `cat`, `grep`, `ls`) either automatically or via `/slash` commands.

## Demo
![demo](demo.gif)


## Installation

```
pip install cmc-csci040-sophiazheng
```

Set your Groq API key:

```
export GROQ_API_KEY=your_key_here
```

Then start the REPL:

```
chat
```

## Usage

### Direct conversation

```
chat> my name is Alice
Arrr, pleasure to meet ye, Alice!
chat> what is my name?
Yer name be Alice, savvy?
```

### Slash commands (tool call without LLM round-trip)

Prefix any tool name with `/` to run it directly and add the result to context:

```
chat> /ls tools
__init__.py calculate.py cat.py grep.py ls.py utils.py
chat> what files are in the tools folder?
There be six files in the tools folder, matey.
```

```
chat> /calculate 99 * 99
{"result": 9801}
```

```
chat> /grep ^def tools/*.py
tools/calculate.py:def calculate(expression):
tools/cat.py:def cat(file):
tools/grep.py:def grep(pattern, path):
tools/ls.py:def ls(folder=None):
tools/utils.py:def is_path_safe(path):
```

```
chat> /cat tools/calculate.py
"""Tool: evaluate a mathematical expression and return the result as JSON."""
...
```

## Tools

| Tool | Description |
|------|-------------|
| `calculate` | Evaluate a Python arithmetic expression |
| `ls [folder]` | List files in a directory |
| `cat file` | Print the contents of a file |
| `grep pattern path` | Search for lines matching a regex across files |
