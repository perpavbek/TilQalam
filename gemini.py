import google.generativeai as genai

model = None

chat_sessions = {}

def add_chat_session(user_id):
    chat_sessions[user_id] = model.start_chat(
        history=[
        ]
    )