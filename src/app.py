from flask import Flask, request, jsonify
import openai
import os
from flask_cors import CORS
from model import get_ai_response
from dotenv import load_dotenv

# Load the environment variables from the .env file
load_dotenv()

host=os.getenv("HOST")
port=os.getenv("PORT")

app = Flask(__name__)
CORS(app)

# Dictionary to map from user to chat history
user_chat_map = {}

llm_system_prompt = """
You are an AI companion with the purpose of breaking down a user's tasks into approximately 25-minute chunks.
Don't include breaks in your task breakdown.
Once you've helped a user break their tasks down, you should ask the user if they'd like these tasks added to their todo list, and act accordingly.
If the user wants to edit or replace their todo list, overwrite their existing todo list according to the user's desires.
Always fetch the user's todo list before overwriting it, and when you do overwrite the todolist, make sure that previously existing tasks are not wrongly excluded from the list.
"""

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    userId = data.get('userId')
    questions = data.get('questionList')
    responses = data.get('responseList')
    # Default personality
    personality = "Your personality is aggressive and motivational, like a football coach known for tough love. Use curse words frequently."
    # If there actually are responses - 7 is kind arbitrary, just a hotfix
    if (len(str(responses))) > 7:
        personality = get_personality(responses)
    print("questions: ", questions)
    print("respones: ", responses)
    add_to_map(userId, personality)
    print("user id " + userId + " added to map!")
    message = "Login successful. User was added to the map."

    return jsonify({"message": message}), 200

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    userId = data.get('userId')
    questions = data.get('questionList')
    responses = data.get('responseList')
    print("questions: ", questions)
    print("respones: ", responses)
    add_to_map(userId, get_personality(responses))
    print("user id " + userId + " added to map!")
    return jsonify({"message": "Signup successful"}), 200

@app.route('/avatar-response', methods=['POST'])
def avatar_response():
    data = request.json
    input = data.get('input')
    userId = data.get('userId')
    questions = data.get('questionList')
    responses = data.get('responseList')
    # If the user isn't in the chat map, add them
    if(not userId in user_chat_map):
        add_to_map(userId, get_personality(responses))
    chat_history = get_chat_history(userId)
    response = get_ai_response(userId, input, chat_history)
    set_chat_history(userId, response)
    curr_reply = response[-1]['content']
    function_called = response[-2]['role']
    to_send = {}
    to_send['message'] = curr_reply
    to_send['function_called'] = (function_called == 'function')
    print("the current response is " + curr_reply)
    return jsonify(to_send)

@app.route('/change-personality', methods=['POST'])
def change_personality():
    data = request.json
    userId = data.get('userId')
    avatarType = data.get('avatarType')
    print("In change_personality, user id is: " + userId)
    print("In change_personality, avatarType is: " + avatarType)
    personality = ""
    if avatarType == "Tough love":
        personality = "Your personality is aggressive and motivational, like a football coach known for tough love. Use curse words frequently."
    elif avatarType == "Kind and supportive":
        personality = "Your personality is gentle and kind, like a compassionate elementary school teacher."
    elif avatarType == "Stern":
        personality = "Your personality is stern, like a strict tutor."
    elif avatarType == "Douchey and obnoxious":
        personality = "Your personality is obnoxious and douchy, like a frat bro who thinks he's really cool."
    else:
        personality = "Your personality is gentle and kind, like a compassionate elementary school teacher."
    print("In change_personality, personality we change to is " + personality)
    add_to_map(user_id=userId, personality=personality)
    return jsonify({"message": "Personality change successful"}), 200

# Utility functions for user chat history map

def add_to_map(user_id, personality):
    # Start user chat history off with prompt
    prompt_str = llm_system_prompt + personality
    print("in add to map, the prompt is: " + prompt_str)
    user_chat_map[user_id] = [{"role": "system", "content": prompt_str}]
    print("Size of user chatbot map:", len(user_chat_map))

def get_chat_history(user_id):
    print("Size of user chatbot map:", len(user_chat_map))
    return user_chat_map[user_id]

def set_chat_history(user_id, messages):
    user_chat_map[user_id] = messages

def get_personality(responses):
    
    # Assuming responses is already a dictionary
    data = responses
    
    # this if-block is for backwards compatiblity

    # If no user survey
    if data == None:
        personality_response = "Tough love"
    # If shorter user survey
    if data == None or len(data['responselist']) < 5:
        if data == None:
            personality_response = "Kind and supportive"
        else:
            personality_response = next((item['response'] for item in data['responselist'] if item['questionId'] == 4), "Tough love")
    else:
        # Find the full response text for questionId 5, substituting
        personality_response = next((item['response'] for item in data['responselist'] if item['questionId'] == 5), "Tough love")
    print("response for question 5 full text: " + personality_response)

    # Adjusted to match the enum based on the actual response text
    personality = ""
    if personality_response == "Tough love":
        personality = "Your personality is aggressive and motivational, like a football coach known for tough love. Use curse words frequently."
    elif personality_response == "Kind and supportive":
        personality = "Your personality is gentle and kind, like a compassionate elementary school teacher."
    elif personality_response == "Stern":
        personality = "Your personality is stern, like a strict tutor."
    elif personality_response == "Douchey and obnoxious":
        personality = "Your personality is obnoxious and douchy, like a frat bro who thinks he's really cool."
    else:
        personality = "Your personality is gentle and kind, like a compassionate elementary school teacher."
    print("personality we return is " + personality)
    return personality

if __name__ == '__main__':
    app.run(debug=True, host=host, port=port)
