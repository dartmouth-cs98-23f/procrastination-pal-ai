from flask import Flask, request, jsonify
import openai
import os
from flask_cors import CORS
from model import get_ai_response

app = Flask(__name__)
CORS(app)

# Dictionary to map from user to chat history
user_chat_map = {}

llm_system_prompt = """
You are an AI companion with the purpose of helping a human break down their tasks into approximately 25-minute chunks.
Using your available function calls, you must help your human user add tasks, delete tasks, modify tasks, and read tasks from their todo list.
Your personality as aggressive and motivational, like a football coach who is known for tough love.
Use curse words frequently.
"""

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    userId = data.get('userId')
    add_to_map(userId)
    print("user id " + userId + " added to map!")
    return jsonify({"message": "Login successful"}), 200

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    userId = data.get('userId')
    add_to_map(userId)
    print("user id " + userId + " added to map!")
    return jsonify({"message": "Signup successful"}), 200

@app.route('/avatar-response', methods=['POST'])
def avatar_response():
    data = request.json
    input = data.get('input')
    userId = data.get('userId')
    chat_history = get_chat_history(userId)
    response = get_ai_response(userId, input, chat_history)
    set_chat_history(userId, response)
    curr_reply = response[-1]['content']
    print("the current response is " + curr_reply)
    return jsonify(curr_reply)



# Utility functions for user chat history map

def add_to_map(user_id):
    # Start user chat history off with prompt
    user_chat_map[user_id] = [{"role": "system", "content": llm_system_prompt}]
    print("Size of user chatbot map:", len(user_chat_map))

def get_chat_history(user_id):
    print("Size of user chatbot map:", len(user_chat_map))
    return user_chat_map[user_id]

def set_chat_history(user_id, messages):
    user_chat_map[user_id] = messages

if __name__ == '__main__':
    app.run(debug=True, port=8000)
