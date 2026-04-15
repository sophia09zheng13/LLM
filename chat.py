"""Pirate-themed command-line chat agent backed by the Groq LLM API.

Run ``python chat.py`` (or the ``chat`` entry-point after installation) to
start an interactive REPL.  Type ``/tool arg1 arg2`` to invoke a tool
directly without an LLM round-trip.
"""

import json

from groq import Groq
from dotenv import load_dotenv

from tools.calculate import calculate, tool_schema as calculate_schema
from tools.cat import cat, tool_schema as cat_schema
from tools.grep import grep, tool_schema as grep_schema
from tools.ls import ls, tool_schema as ls_schema

load_dotenv()

tool_schema = [calculate_schema, ls_schema, cat_schema, grep_schema]

available_functions = {
    "calculate": calculate,
    "ls": ls,
    "cat": cat,
    "grep": grep,
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
        self.MODEL = "openai/gpt-oss-120b"
        self.messages = [{"role": "system", "content": _SYSTEM_PROMPT}]

    def send_message(self, message, temperature=0.0):
        """Append *message* to history, call the LLM, execute any tool calls, and return the reply.

        If the model requests a ``cat`` tool call the raw file contents are
        returned directly (no pirate rephrasing).  All other tool results are
        fed back to the model for a final natural-language response.

        Unit tests mock the Groq client so no API key is required.

        No-tool-call path (model replies directly):
        >>> import unittest.mock, types
        >>> fake_msg = types.SimpleNamespace(tool_calls=None, content='Arrr!')
        >>> fake_resp = types.SimpleNamespace(choices=[types.SimpleNamespace(message=fake_msg)])
        >>> with unittest.mock.patch('chat.Groq') as MockGroq:
        ...     MockGroq.return_value.chat.completions.create.return_value = fake_resp
        ...     c = Chat()
        ...     c.send_message('hello')
        'Arrr!'

        Tool-call path — non-cat tool (calculate), expects second API call:
        >>> tool_call = types.SimpleNamespace(
        ...     id='tc1',
        ...     function=types.SimpleNamespace(name='calculate', arguments='{"expression": "1+1"}')
        ... )
        >>> fake_tool_msg = types.SimpleNamespace(tool_calls=[tool_call], content=None)
        >>> fake_tool_resp = types.SimpleNamespace(choices=[types.SimpleNamespace(message=fake_tool_msg)])
        >>> fake_final_msg = types.SimpleNamespace(content='The answer be 2!')
        >>> fake_final_resp = types.SimpleNamespace(choices=[types.SimpleNamespace(message=fake_final_msg)])
        >>> with unittest.mock.patch('chat.Groq') as MockGroq:
        ...     mock_create = MockGroq.return_value.chat.completions.create
        ...     mock_create.side_effect = [fake_tool_resp, fake_final_resp]
        ...     c = Chat()
        ...     c.send_message('what is 1+1?')  # doctest: +ELLIPSIS
        [tool] function_name=calculate, function_args=...
        'The answer be 2!'

        Tool-call path — cat tool returns raw file content without second API call:
        >>> cat_call = types.SimpleNamespace(
        ...     id='tc2',
        ...     function=types.SimpleNamespace(name='cat', arguments='{"file": "tools/calculate.py"}')
        ... )
        >>> fake_cat_msg = types.SimpleNamespace(tool_calls=[cat_call], content=None)
        >>> fake_cat_resp = types.SimpleNamespace(choices=[types.SimpleNamespace(message=fake_cat_msg)])
        >>> with unittest.mock.patch('chat.Groq') as MockGroq:
        ...     MockGroq.return_value.chat.completions.create.return_value = fake_cat_resp
        ...     c = Chat()
        ...     result = c.send_message('show me calculate.py')  # doctest: +ELLIPSIS
        [tool] function_name=cat, function_args=...
        >>> 'def calculate' in result
        True
        """
        self.messages.append({'role': 'user', 'content': message})

        chat_completion = self.client.chat.completions.create(
            messages=self.messages,
            model=self.MODEL,
            temperature=temperature,
            seed=0,
            tools=tool_schema,
            tool_choice="auto",
        )
        response_message = chat_completion.choices[0].message
        tool_calls = response_message.tool_calls

        if tool_calls:
            self.messages.append(response_message)

            raw_output = None
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)
                print(f"[tool] function_name={function_name}, function_args={function_args}")

                if function_name == "cat":
                    raw_output = function_response

                self.messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                })

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

        result = chat_completion.choices[0].message.content
        self.messages.append({'role': 'assistant', 'content': result})
        return result


def repl(temperature=0.0):
    """Run an interactive read-eval-print loop.

    Lines that start with ``/`` are treated as direct tool invocations and
    bypass the LLM entirely.  The tool output is printed immediately and
    added to the conversation history so the model has context for follow-up
    questions.

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
    __init__.py calculate.py cat.py grep.py ls.py utils.py
    chat> Goodbye.
    Farewell.
    <BLANKLINE>
    """
    import readline  # noqa: F401 — enables arrow-key history on supported platforms
    chat = Chat()
    try:
        while True:
            user_input = input('chat> ')
            if user_input.startswith('/'):
                parts = user_input[1:].split()
                command = parts[0]
                args = parts[1:]
                if command in available_functions:
                    result = available_functions[command](*args)
                    print(result)
                    chat.messages.append({'role': 'user', 'content': user_input})
                    chat.messages.append({'role': 'assistant', 'content': result})
                else:
                    print(f"Unknown command: /{command}")
            else:
                response = chat.send_message(user_input)
                print(response)
    except (KeyboardInterrupt, EOFError):
        print()


if __name__ == '__main__':
    repl()
