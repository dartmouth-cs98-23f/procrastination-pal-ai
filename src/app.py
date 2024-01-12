from flask import Flask, request, jsonify
import openai
import os
from flask_cors import CORS
from model import get_ai_response

app = Flask(__name__)
CORS(app)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Dictionary to map from user to chat history
user_chat_map = {}

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
    return jsonify(response)



# Utility functions for user chat history map

def add_to_map(user_id):
    user_chat_map[user_id] = []
    print("Size of user chatbot map:", len(user_chat_map))

def get_chat_history(user_id):
    print("Size of user chatbot map:", len(user_chat_map))
    return user_chat_map.get(user_id, "")

def set_chat_history(user_id, messages):
    user_chat_map[user_id] = messages

if __name__ == '__main__':
    app.run(debug=True, port=8000)
