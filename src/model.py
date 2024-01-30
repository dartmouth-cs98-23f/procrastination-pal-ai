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
function_call_limit = 3



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


def todo_list_append(tasks: str = None, user_id: str = None):
    """Break down the string of user tasks into tasks, and append them to the user's todo list"""

    # Get the tasks in json format
    json_to_append = tasks_to_json(tasks)
    # Send this to the actual backend
    # Headers to specify that the request body is JSON
    headers = {
        'Content-Type': 'application/json'
    }
    data = json_to_append
    data["userId"] = user_id
    # Make the POST request
    response = requests.post(node_backend_api+'/todo-list-append', json=data, headers=headers)

    # Print the response from the server
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
    # Directly parse the JSON response
    response_data = response.json()
    message = response_data['message']
    return message

def todo_list_overwrite(tasks: str = None, user_id: str = None):
    """Break down the string of user tasks into tasks, and overwrite the user's existing todolist with these tasks"""

    # Get the tasks in json format
    json_to_append = tasks_to_json(tasks)
    # Send this to the actual backend
    # Headers to specify that the request body is JSON
    headers = {
        'Content-Type': 'application/json'
    }
    data = json_to_append
    data["userId"] = user_id
    # Make the POST request
    response = requests.post(node_backend_api+'/todo-list-overwrite', json=data, headers=headers)

    # Print the response from the server
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
    # Directly parse the JSON response
    response_data = response.json()
    message = response_data['message']
    return message

def todo_list_fetch(user_id: str = None):
    """Fetches a user's current todo list"""

    headers = {
        'Content-Type': 'application/json'
    }

    # Make the GET request
    response = requests.get(node_backend_api+'/user/'+user_id, headers=headers)

    # Print the response from the server
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
    # Directly parse the JSON response
    response_data = response.json()
    todolist = response_data['todolist']['tasklist']
    return todolist

tools = [
  {
    "type": "function",
    "function": {
      "name": "todo_list_append",
      "description": "Takes a string containing all user tasks, and appends them to the user's todo list in an organized format.",
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
  },
  {
    "type": "function",
    "function": {
      "name": "todo_list_overwrite",
      "description": "Takes a string containing all user tasks, and overwrites the user's existing todo list with these tasks.",
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
  },
  {
    "type": "function",
    "function": {
      "name": "todo_list_fetch",
      "description": "Fetches a JSON-formatted string of the user's current todo list.",
      "parameters": {
      },
    }
  }

]


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
    
    print("choices length: " + str(len(res.choices)))
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
        if function_name == "todo_list_append":
            args = json.loads(response.tool_calls[0].function.arguments)
            print("tasks is " + args.get("tasks"))
            output = todo_list_append(
                tasks=args.get("tasks"),
                user_id=userId,   
            )
            print("output is " + str(output))
            messages.append({ "role": "function", "name": "todo_list_append", "content": output})
        elif function_name == "todo_list_overwrite":
            args = json.loads(response.tool_calls[0].function.arguments)
            print("tasks is " + args.get("tasks"))
            output = todo_list_overwrite(
                tasks=args.get("tasks"),
                user_id=userId,   
            )
            print("output is " + str(output))
            messages.append({ "role": "function", "name": "todo_list_overwrite", "content": output})
        elif function_name == "todo_list_fetch":
            output = todo_list_fetch(
                user_id=userId,   
            )
            messages.append({ "role": "function", "name": "todo_list_fetch", "content": json.dumps(output)})
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
        print("call count is " + str(call_count))
        # If we just appended or overwrote todo list, or at our tool-using limit, no need for more tool usage - just give textual response
        if messages[-1]['name'] == "todo_list_append" or messages[-1]['name'] == "todo_list_overwrite" or call_count >= function_call_limit:
            complete(userId=userId, messages=messages, tool_choice="none")
        else:
            complete(userId=userId, messages=messages, tool_choice="auto")
    
    # return all messages
    return messages


def tasks_to_json(tasks : str = None):
    """Given a string of tasks, parses them into a json object that can be added to a user's todo list"""

    prompt_str = """
    A human has provided you with a statement about the tasks that they have to do. 
    This statement may or may not contain the lengths of said tasks. 
    Your job is to parse the list of tasks into a JSON object, the structure of which will be described below.
    When parsing the list, you should take the liberty to break down user tasks into subtasks, and ensure that no task is estimated to take longer than 25 minutes.
    Do not include breaks.

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
    return json.loads(chat_message)