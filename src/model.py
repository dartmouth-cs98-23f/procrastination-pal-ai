# Mostly referencing https://semaphoreci.com/blog/function-calling
# OpenAI model references https://ihsavru.medium.com/how-to-build-your-own-custom-chatgpt-using-python-openai-78e470d1540e

from openai import OpenAI
import tiktoken
import requests
import json
import os
from dotenv import load_dotenv
import sys

# Load the environment variables from the .env file
load_dotenv()

my_api_key=os.getenv("OPENAI_API_KEY")
node_backend_api=os.getenv("NODE_BACKEND_API")

client = OpenAI(api_key=my_api_key)
llm_model = "gpt-4-1106-preview"
llm_max_tokens = 31000
encoding_model_messages = "gpt-4-0613"
encoding_model_strings = "cl100k_base"
function_call_limit = 5



def num_tokens_from_messages(messages):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(encoding_model_messages)
    except KeyError:
        encoding = tiktoken.get_encoding(encoding_model_strings)

    num_tokens = 0
    for message in messages:
        num_tokens += 4
        for key, value in message.items():
            num_tokens += len(encoding.encode(str(value)))
            if key == "name":
                num_tokens += -1
    num_tokens += 2
    return num_tokens


def make_todo_list(tasks: str = None, user_id: str = None):
    """Break down the string of user tasks into a todo list for the user"""

    prompt_str = """
    A human has provided you with a statement about the tasks that they have to do. 
    This statement may or may not contain the lengths of said tasks. 
    Your job is to parse the list of tasks into a JSON object, the structure of which will be described below.
    When parsing the list, you should take the liberty to break down user tasks into subtasks, and ensure that no task is estimated to take longer than 25 minutes.

    Return a JSON object that contains a tasklist object, which is a list of todo objects. Todo objects look like this:
    - task: The task that the human must complete
    - length: In minutes, the amount of time that this task will take
    - completed: Whether the task is complete or not (this field should always be set to false)

    Example:

    {
    "tasklist": {
    {
    "task": "Do first math problem",
    "length": "15",
    "completed": "false"
    },
    {
    "task": "Do first math problem",
    "length": "15",
    "completed": "false"
    },
    }
    }
    """


    messages_temp = [
    {"role": "system", "content": prompt_str},
    ]

    message = tasks

    # Add new message to the list
    messages_temp.append({"role": "user", "content": message})

    # Request model for chat completion
    response = client.chat.completions.create(model="gpt-4-1106-preview",
    messages=messages_temp,
    response_format={ "type": "json_object" })

    # Print the response and add it to the messages list
    chat_message = response.choices[0].message.content
    print(f"Bot: {chat_message}")
    # Send this to the actual backend
    # Headers to specify that the request body is JSON
    headers = {
        'Content-Type': 'application/json'
    }
    data = json.loads(chat_message)
    data["userId"] = user_id
    # Make the POST request
    response = requests.post(node_backend_api+'/modify-todo-list', json=data, headers=headers)

    # Print the response from the server
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
    # Directly parse the JSON response
    response_data = response.json()
    todolist = response_data['todolist']
    return todolist

tools = [
  {
    "type": "function",
    "function": {
      "name": "make_todo_list",
      "description": "Given one or more tasks, adds these tasks to the user's todo list. For a given collection of tasks, only call this function once, instead of calling it for each task separately. Do not provide inputs that you have already added to the user's todo list.",
      "parameters": {
        "type": "object",
        "properties": {
          "tasks": {
                "type": "string",
                "description": "String of user tasks and their estimated time to complete",
            },
        },
        "required": [],
      },
    }
  }
]

# signature_add_todo = {
#     "name": "add_todo",
#     "description" : "Give a task and the length, add it into the users todolist. Should be called when a task and a length is provided",
#     "parameters":{
#         "type": "object",
#     }
# }


def complete(userId, messages, tool_choice: str = "auto"):
    """Fetch completion from OpenAI's GPT"""

    # delete older completions to keep conversation under token limit
    while num_tokens_from_messages(messages) >= llm_max_tokens:
        messages.pop(0)

    print('Working...')
    res = client.chat.completions.create(model=llm_model,
    messages=messages,
    tools=tools,
    tool_choice=tool_choice)
    
    response = res.choices[0].message
    content = response.content 
    role = response.role
    print("role is " + role)
    finish_reason = res.choices[0].finish_reason
    print("finish reason is " + finish_reason)

    # call functions requested by the model
    if finish_reason == "tool_calls":
        print("the finish reason is tool call!")
        function_name = response.tool_calls[0].function.name
        print("function name is " + function_name)
        if function_name == "make_todo_list":
            args = json.loads(response.tool_calls[0].function.arguments)
            print("tasks is " + args.get("tasks"))
            output = make_todo_list(
                tasks=args.get("tasks"),
                user_id=userId,   
            )
            print("output is " + json.dumps(output))
            messages.append({ "role": "function", "name": "make_todo_list", "content": json.dumps(output)})
    else:
        messages.append({'role': role, 'content': content})
    
    print("trying to access messages woooo! After running complete")
    for thing in messages:
        print(thing)
    

def get_ai_response(userId, input, messages):

    messages.append({"role": "user", "content": input})
    complete(userId=userId, messages=messages)

    # the LLM can chain function calls, this implements a limit
    call_count = 0
    while messages[-1]['role'] == "function":
        call_count = call_count + 1
        if call_count < function_call_limit:
            complete(userId=userId, messages=messages)
        else:
            complete(userId=userId, messages=messages, tool_choice="none")
    
    # return all messages
    return messages