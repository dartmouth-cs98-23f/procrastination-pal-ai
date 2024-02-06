from flask import Flask, request, jsonify
import openai
import os
from flask_cors import CORS
from model import get_ai_response
from dotenv import load_dotenv
from enum import Enum

# Load the environment variables from the .env file
load_dotenv()

host=os.getenv("HOST")
port=os.getenv("PORT")

app = Flask(__name__)
CORS(app)

# Dictionary to map from user to chat history
user_chat_map = {}

# Define an enum for user's desired personality type
class PersonalityType(Enum):
    TOUGH_LOVE = 'Tough love, like a football coach' 
    KIND_AND_SUPPORTIVE = 'Kind and supportive, like an elementary school teacher'
    STERN = 'Stern, like an old and wise tutor'
    DOUCHEY_AND_OBNOXIOUS = 'Douchey and obnoxious, like a frat bro'

llm_system_prompt = """
You are an AI companion with the purpose of breaking down a user's tasks into approximately 25-minute chunks.
Don't include breaks in your task breakdown.
Once you've helped a user break their tasks down, you should ask the user if they'd like these tasks added to their todo list, and act accordingly.
If the user wants to edit or replace their todo list, overwrite their existing todo list according to the user's desires.
"""

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    userId = data.get('userId')
    questions = data.get('questionList')
    responses = data.get('responseList')
    print("questions: ", questions)
    print("respones: ", responses)
    add_to_map(userId, get_personality(responses))
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

# Utility functions for user chat history map

def add_to_map(user_id, personality):
    # Start user chat history off with prompt
    user_chat_map[user_id] = [{"role": "system", "content": llm_system_prompt + "\n" + personality}]
    print("Size of user chatbot map:", len(user_chat_map))

def get_chat_history(user_id):
    print("Size of user chatbot map:", len(user_chat_map))
    return user_chat_map[user_id]

def set_chat_history(user_id, messages):
    user_chat_map[user_id] = messages

def get_personality(responses):
    # Assuming responses is already a dictionary
    data = responses

    # Find the full response text for questionId 4
    response_for_question_4_full_text = next((item['response'] for item in data['responselist'] if item['questionId'] == 4), None)

    # Adjusted to match the enum based on the actual response text
    personality = ""
    if response_for_question_4_full_text:
        # Normalize the response to match with enum values
        normalized_response = response_for_question_4_full_text.strip().capitalize()

        if normalized_response in (pt.value for pt in PersonalityType):
            if normalized_response == PersonalityType.TOUGH_LOVE.value:
                personality = "Your personality is aggressive and motivational, like a football coach known for tough love. Use curse words frequently."
            elif normalized_response == PersonalityType.KIND_AND_SUPPORTIVE.value:
                personality = "Your personality is gentle and kind, like a compassionate elementary school teacher."
            elif normalized_response == PersonalityType.STERN.value:
                personality = "Your personality is stern, like a strict tutor."
            elif normalized_response == PersonalityType.DOUCHEY_AND_OBNOXIOUS.value:
                personality = "Your personality is obnoxious and douchy, like a frat bro who thinks he's really cool."
        else:
            personality = "Personality not found based on the response."

    return personality

if __name__ == '__main__':
    app.run(debug=True, host=host, port=port)
