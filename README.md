# Sophia's Personal LLM

[![tests](https://github.com/sophia09zheng13/LLM/actions/workflows/tests.yml/badge.svg)](https://github.com/sophia09zheng13/LLM/actions/workflows/tests.yml)
[![integration-tests](https://github.com/sophia09zheng13/LLM/actions/workflows/integration-tests.yml/badge.svg)](https://github.com/sophia09zheng13/LLM/actions/workflows/integration-tests.yml)
[![PyPI](https://img.shields.io/pypi/v/cmc-csci040-sophiazheng)](https://pypi.org/project/cmc-csci040-sophiazheng/)
[![flake8](https://github.com/sophia09zheng13/LLM/actions/workflows/flake8.yml/badge.svg)](https://github.com/sophia09zheng13/LLM/actions/workflows/flake8.yml)
[![codecov](https://codecov.io/gh/sophia09zheng13/LLM/branch/main/graph/badge.svg)](https://codecov.io/gh/sophia09zheng13/LLM)

A pirate-themed command-line chat agent powered by Groq's LLM API. The agent
can answer questions, remember conversational context, and call built-in tools
(`calculate`, `cat`, `grep`, `ls`) either automatically or via `/slash` commands.

![demo](demo.gif)


## Installation

Every code block needs a sentence introducing it
```
$ pip install cmc-csci040-sophiazheng
```

Set your Groq API key:

```
$ export GROQ_API_KEY=your_key_here
```

<!-- don't have a $chat command ever without also showing the output; just go directly into usage here -->

## Usage

The agent remembers information across messages in the same session, so you can refer back to things you said earlier.

```
chat> my name is Alice
Arrr, pleasure to meet ye, Alice!
chat> what is my name?
Yer name be Alice, savvy?
```

### Slash commands (tool call without LLM round-trip)
<!-- these are all excellent examples here; nice job! -->

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

## Tools

| Tool | Description |
|------|-------------|
| `calculate` | Evaluate a Python arithmetic expression |
| `ls [folder]` | List files in a directory |
| `cat file` | Print the contents of a file |
| `grep pattern path` | Search for lines matching a regex across files |
| `compact` | Summarize conversation history and reset to a compact summary (slash command only) |
