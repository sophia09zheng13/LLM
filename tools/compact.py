"""Tool: summarize the current conversation history into 1-5 lines using a Chat subagent."""


def compact(messages, _Chat=None):
    """Summarize *messages* into 1-5 lines of plain text using a Chat subagent.

    Creates a fresh ``Chat`` instance (a subagent) whose sole job is to read
    the current conversation and write a compact summary.  The caller should
    replace its ``messages`` list with a single entry containing the returned
    summary so that subsequent LLM calls use far fewer tokens.

    The import of ``Chat`` is deferred to the function body to avoid a
    circular import (``chat`` imports this module; this module imports
    ``chat``).  Pass *_Chat* in tests to inject a mock class and avoid
    importing ``chat`` entirely.

    >>> import unittest.mock
    >>> mock_cls = unittest.mock.MagicMock()
    >>> mock_cls.return_value.send_message.return_value = 'User asked what 2+2 is. The answer is 4.'
    >>> result = compact(
    ...     [
    ...         {'role': 'system', 'content': 'Talk like a pirate.'},
    ...         {'role': 'user', 'content': 'what is 2+2?'},
    ...         {'role': 'assistant', 'content': 'Arrr, it be 4!'},
    ...     ],
    ...     _Chat=mock_cls,
    ... )
    >>> result
    'User asked what 2+2 is. The answer is 4.'

    Only user and assistant turns are included in the prompt sent to the subagent:

    >>> call_args = mock_cls.return_value.send_message.call_args[0][0]
    >>> 'USER: what is 2+2?' in call_args
    True
    >>> 'ASSISTANT: Arrr, it be 4!' in call_args
    True
    >>> 'system' not in call_args
    True
    """
    if _Chat is None:
        from chat import Chat  # lazy import to avoid circular dependency
        _Chat = Chat

    conversation_lines = []
    for m in messages:
        if m['role'] in ('user', 'assistant') and m.get('content'):
            conversation_lines.append(f"{m['role'].upper()}: {m['content']}")
    conversation_text = '\n'.join(conversation_lines)

    subagent = _Chat()
    summary = subagent.send_message(
        "Summarize this conversation in 1-5 lines of plain text, "
        "capturing only the key facts and context needed to continue it. "
        "Do NOT use pirate speak — write plain, clear prose:\n\n"
        + conversation_text
    )
    return summary
