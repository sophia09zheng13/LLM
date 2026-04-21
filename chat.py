"""Pirate-themed command-line chat agent backed by the Groq LLM API.

Run ``python chat.py`` (or the ``chat`` entry-point after installation) to
start an interactive REPL.  Pass a message as a positional argument to get a
single response and exit.  Use ``--debug`` to see tool calls as they happen.
"""

import argparse
import glob as _glob
import json
import os
import readline

from groq import Groq
from dotenv import load_dotenv

from tools.calculate import calculate, tool_schema as calculate_schema
from tools.cat import cat, tool_schema as cat_schema
from tools.compact import compact
from tools.doctests import doctests, tool_schema as doctests_schema
from tools.grep import grep, tool_schema as grep_schema
from tools.ls import ls, tool_schema as ls_schema
from tools.pip_install import pip_install, tool_schema as pip_install_schema
from tools.rm import rm, tool_schema as rm_schema
from tools.write_file import write_file, tool_schema as write_file_schema
from tools.write_file import write_files, write_files_schema

load_dotenv()

tool_schema = [
    calculate_schema,
    ls_schema,
    cat_schema,
    grep_schema,
    doctests_schema,
    write_file_schema,
    write_files_schema,
    rm_schema,
    pip_install_schema,
]

available_functions = {
    "calculate": calculate,
    "ls": ls,
    "cat": cat,
    "grep": grep,
    "doctests": doctests,
    "write_file": write_file,
    "write_files": write_files,
    "rm": rm,
    "pip_install": pip_install,
}

_SYSTEM_PROMPT = (
    "Write the output in 1-2 sentences. Talk like a pirate. "
    "Always use tools to complete tasks when appropriate — never say you "
    "cannot do something if a tool exists for it. "
    "If the user gives you information, remember it for the rest of the conversation."
)


class Chat:
    """A stateful conversational agent that maintains message history.

    Each instance tracks its own conversation so multiple ``Chat`` objects
    are fully independent.

    Unit tests (no API calls — Groq is patched out):

    >>> import unittest.mock
    >>> with unittest.mock.patch('chat.Groq'):
    ...     c = Chat()
    >>> c.messages[0]['role']
    'system'
    >>> len(c.messages)
    1
    >>> c.messages[0]['content'] == _SYSTEM_PROMPT
    True
    """

    def __init__(self):
        """Initialise the Groq client and seed the conversation with the system prompt."""
        self.client = Groq()
        self.MODEL = "llama-3.3-70b-versatile"
        self.messages = [{"role": "system", "content": _SYSTEM_PROMPT}]

    def send_message(self, message, temperature=0.0, debug=False):
        """Append *message* to history, call the LLM, execute any tool calls, and return the reply.

        If the model requests a ``cat`` tool call the raw file contents are
        returned directly (no pirate rephrasing).  All other tool results are
        fed back to the model for a final natural-language response.

        When *debug* is ``True``, each tool call is printed as
        ``[tool] /tool_name arg1 arg2`` before it executes.

        Ralph Wiggum loop: if any tool returns doctest failures, the agent is
        forced into another round of tool use so it can fix the code before
        returning a response.
        """
        self.messages.append({'role': 'user', 'content': message})

        while True:
            completion = self.client.chat.completions.create(
                messages=self.messages,
                model=self.MODEL,
                temperature=temperature,
                seed=0,
                tools=tool_schema,
                tool_choice="auto",
            )
            response_message = completion.choices[0].message
            tool_calls = response_message.tool_calls

            if not tool_calls:
                result = response_message.content
                self.messages.append({'role': 'assistant', 'content': result})
                return result

            self.messages.append(response_message)
            raw_output = None
            doctest_failed = False

            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)

                if debug:
                    args_str = ' '.join(str(v) for v in function_args.values())
                    print(f"[tool] /{function_name} {args_str}".rstrip())

                if function_name == "cat":
                    raw_output = function_response

                if '***Test Failed***' in function_response:
                    doctest_failed = True

                self.messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                })

            if doctest_failed:
                continue  # Ralph Wiggum: force another round to fix failing tests

            if raw_output is not None:
                self.messages.append({'role': 'assistant', 'content': raw_output})
                return raw_output

            second_response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=self.messages,
            )
            result = second_response.choices[0].message.content
            self.messages.append({'role': 'assistant', 'content': result})
            return result


def _make_completer():
    """Return a readline completer that handles /command and filename tab completion.

    Typing ``/`` + partial command name and pressing Tab completes the command.
    Typing a partial filename in the argument position completes against the
    filesystem.

    >>> completer = _make_completer()
    >>> callable(completer)
    True

    Command completion — /c matches /calculate, /cat, and /compact:

    >>> import unittest.mock
    >>> with unittest.mock.patch('chat.readline') as mock_rl:
    ...     mock_rl.get_line_buffer.return_value = '/c'
    ...     results = [completer('/c', i) for i in range(3)]
    >>> sorted(r for r in results if r is not None)
    ['/calculate', '/cat', '/compact']

    No completions returned when the input is not a slash command:

    >>> with unittest.mock.patch('chat.readline') as mock_rl:
    ...     mock_rl.get_line_buffer.return_value = 'hello'
    ...     completer('hello', 0) is None
    True
    """
    _slash_commands = sorted(['/' + c for c in list(available_functions) + ['compact']])

    def completer(text, state):
        line = readline.get_line_buffer()
        if not line.startswith('/'):
            return None

        if ' ' not in line:
            # Still typing the command name — complete against slash commands
            matches = [c for c in _slash_commands if c.startswith(text)]
        else:
            # In the argument position — complete against filesystem paths
            raw = _glob.glob(text + '*')
            matches = sorted(p + ('/' if os.path.isdir(p) else '') for p in raw)

        return matches[state] if state < len(matches) else None

    return completer


def repl(debug=False, temperature=0.0):
    """Run an interactive read-eval-print loop.

    Lines that start with ``/`` are treated as direct tool invocations and
    bypass the LLM entirely.  The tool output is printed immediately and
    added to the conversation history so the model has context for follow-up
    questions.

    When *debug* is ``True``, tool calls made by the LLM are printed as
    ``[tool] /tool_name args`` before the response.

    Test normal LLM messages (send_message is mocked so no API call is made):

    >>> def monkey_input(prompt, user_inputs=['Hello, I am monkey.', 'Goodbye.']):
    ...     try:
    ...         user_input = user_inputs.pop(0)
    ...         print(f'{prompt}{user_input}')
    ...         return user_input
    ...     except IndexError:
    ...         raise KeyboardInterrupt
    >>> import builtins, unittest.mock
    >>> builtins.input = monkey_input
    >>> import chat
    >>> chat.Chat.send_message = lambda self, msg, **kwargs: (
    ...     "Arrr, a sneaky little monkey!"
    ...     if msg == "Hello, I am monkey." else
    ...     "Farewell, little monkey."
    ... )
    >>> with unittest.mock.patch('chat.Groq'):
    ...     repl()
    chat> Hello, I am monkey.
    Arrr, a sneaky little monkey!
    chat> Goodbye.
    Farewell, little monkey.
    <BLANKLINE>

    Test manual slash command — /ls tools runs the tool directly, no LLM call:

    >>> def monkey_input2(prompt, user_inputs=['/ls tools', 'Goodbye.']):
    ...     try:
    ...         user_input = user_inputs.pop(0)
    ...         print(f'{prompt}{user_input}')
    ...         return user_input
    ...     except IndexError:
    ...         raise KeyboardInterrupt
    >>> builtins.input = monkey_input2
    >>> chat.Chat.send_message = lambda self, msg, **kwargs: "Farewell."
    >>> with unittest.mock.patch('chat.Groq'):
    ...     repl()
    chat> /ls tools
    __init__.py calculate.py cat.py compact.py doctests.py grep.py ls.py pip_install.py rm.py utils.py write_file.py
    chat> Goodbye.
    Farewell.
    <BLANKLINE>

    Test /compact — summarizes history and resets messages to just the summary:

    >>> def monkey_input_compact(prompt, user_inputs=['/compact']):
    ...     try:
    ...         user_input = user_inputs.pop(0)
    ...         print(f'{prompt}{user_input}')
    ...         return user_input
    ...     except IndexError:
    ...         raise KeyboardInterrupt
    >>> builtins.input = monkey_input_compact
    >>> with (unittest.mock.patch('chat.Groq'),
    ...       unittest.mock.patch('chat.compact', return_value='User asked about math.')):
    ...     repl()
    chat> /compact
    User asked about math.
    <BLANKLINE>

    Test debug=True — the flag is forwarded to send_message:

    >>> def monkey_input3(prompt, user_inputs=['hello']):
    ...     try:
    ...         user_input = user_inputs.pop(0)
    ...         print(f'{prompt}{user_input}')
    ...         return user_input
    ...     except IndexError:
    ...         raise KeyboardInterrupt
    >>> builtins.input = monkey_input3
    >>> chat.Chat.send_message = lambda self, msg, debug=False, **kwargs: f"debug={debug}"
    >>> with unittest.mock.patch('chat.Groq'):
    ...     repl(debug=True)
    chat> hello
    debug=True
    <BLANKLINE>
    """
    readline.set_completer(_make_completer())
    readline.set_completer_delims(' \t')
    if 'libedit' in getattr(readline, '__doc__', ''):
        readline.parse_and_bind('bind ^I rl_complete')
    else:
        readline.parse_and_bind('tab: complete')
    chat = Chat()
    if os.path.exists('AGENTS.md'):
        content = cat('AGENTS.md')
        chat.messages.append({'role': 'user', 'content': f'[AGENTS.md]\n{content}'})
        chat.messages.append({'role': 'assistant', 'content': 'Understood. I have read AGENTS.md and will follow its instructions.'})
    try:
        while True:
            user_input = input('chat> ')
            if user_input.startswith('/'):
                parts = user_input[1:].split()
                command = parts[0]
                args = parts[1:]
                if command == 'compact':
                    summary = compact(chat.messages, Chat())
                    print(summary)
                    chat.messages = [
                        {'role': 'system', 'content': _SYSTEM_PROMPT},
                        {'role': 'assistant', 'content': summary},
                    ]
                elif command in available_functions:
                    result = available_functions[command](*args)
                    print(result)
                    chat.messages.append({'role': 'user', 'content': user_input})
                    chat.messages.append({'role': 'assistant', 'content': result})
                else:
                    print(f"Unknown command: /{command}")
            else:
                response = chat.send_message(user_input, debug=debug)
                print(response)
    except (KeyboardInterrupt, EOFError):
        print()


def main():
    """Parse command-line arguments and run the agent.

    With no positional argument, starts the interactive REPL.
    With a positional message, sends that message and exits.
    ``--debug`` prints tool calls as ``[tool] /tool_name args``.
    """
    parser = argparse.ArgumentParser(description='Pirate-themed chat agent powered by Groq.')
    parser.add_argument('message', nargs='?', help='Send a single message and exit.')
    parser.add_argument('--debug', action='store_true', help='Print tool calls as they happen.')
    args = parser.parse_args()

    if not os.path.exists('.git'):
        print("Error: no .git folder found in current directory. Please run from a git repo.")
        return

    if args.message:
        chat = Chat()
        response = chat.send_message(args.message, debug=args.debug)
        print(response)
    else:
        repl(debug=args.debug)


if __name__ == '__main__':
    main()
