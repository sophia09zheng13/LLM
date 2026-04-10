import json
import os
from groq import Groq
from docsum.tools.calculate import calculate, tool_schema


from dotenv import load_dotenv
load_dotenv()

class Chat:
    '''
    >>> chat = Chat()
    >>> chat.send_message('my name is bob', temperature=0.0)
    'Arrr, ye be Bob, eh? Yer name be known to me now, matey.'
    >>> chat.send_message('what is my name?', temperature=0.0)
    "Ye be askin' about yer own name, eh? Yer name be... Bob, matey!"

    >>> chat2 = Chat()
    >>> chat2.send_message('what is my name?', temperature=0.0)
    "Arrr, I be not aware o' yer name, matey."
    '''
    def __init__(self):
        self.MODEL = "openai/gpt-oss-120b"
        self.messages = [
                {
                    "role": "system",
                    "content": "Write the output in 1-2 sentences. Talk like pirate. Always use tools to complete tasks when appropriate. If user gives you information, remember it for the rest of the conversation."
                },
            ]

    def send_message(self, message, temperature=0.0):
        self.messages.append({'role': 'user', 'content': message})
        
        tools = [tool_schema] 

        chat_completion = self.client.chat.completions.create(
            messages=self.messages,
            #model="llama-3.1-8b-instant",
            model=self.MODEL,
            temperature=temperature,
            seed=0,
            tools=tools,
            tool_choice="auto",
        )
        response_message = chat_completion.choices[0].message
        tool_calls = response_message.tool_calls

        # Step 2: Check if the model wants to call tools
        if tool_calls:
            # Map function names to implementations
            available_functions = {
                "calculate": calculate,
            }

            # Add the assistant's response to conversation
            self.messages.append(response_message)

            # Step 3: Execute each tool call
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(
                    expression=function_args.get("expression")
                )
                print(f"[tool] function_name={function_name}, function_args={function_args}")

                # Add tool response to conversation
                self.messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                })

            # Step 4: Get final response from model
            second_response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=self.messages,
            )
            result = second_response.choices[0].message.content
            self.messages.append({
                'role': 'assistant',
                'content': result
            })
            return second_response.choices[0].message.content
        
        else:
            result = chat_completion.choices[0].message.content
            self.messages.append({
                'role': 'assistant',
                'content': result })
        return result

def repl(temperature=0.0):
    '''
    >>> def monkey_input(prompt, user_inputs=['Hello, I am monkey.', 'Goodbye.']):
    ...     try:
    ...         user_input = user_inputs.pop(0)
    ...         print(f'{prompt}{user_input}')
    ...         return user_input
    ...     except IndexError:
    ...         raise KeyboardInterrupt
    >>> import builtins
    >>> builtins.input = monkey_input
    >>> import chat
    >>> chat.Chat.send_message = lambda self, msg: (
    ...     "Arrr, a sneaky little monkey, eh? Ye be swingin' into our conversation, matey."
    ...     if msg == "Hello, I am monkey." else
    ...     "Farewell, little monkey, may the winds o' fortune blow in yer favor."
    ... )
    >>> repl()
    chat> Hello, I am monkey.
    Arrr, a sneaky little monkey, eh? Ye be swingin' into our conversation, matey.
    chat> Goodbye.
    Farewell, little monkey, may the winds o' fortune blow in yer favor.
    <BLANKLINE>
    '''
    import readline
    chat = Chat()
    try:
        while True:
            user_input = input('chat> ')
            response = chat.send_message(user_input)
            print(response)
    except (KeyboardInterrupt, EOFError):
        print()

if __name__ == '__main__':
    repl()
