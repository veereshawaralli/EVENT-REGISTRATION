import google.generativeai as genai
import sys
import os

from decouple import config

def test():
    api_key = config("GEMINI_API_KEY", default="")
    print(f"Loaded key starts with: {api_key[:10]}...")
    if not api_key:
        print("No API key found in .env!")
        return
        
    genai.configure(api_key=api_key)
    
    models = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-2.0-flash-lite', 'gemini-1.5-flash']
    for m in models:
        print(f"Testing model: {m}...")
        try:
            model = genai.GenerativeModel(m)
            chat = model.start_chat()
            res = chat.send_message("Hello!")
            print(f"Success with {m}: {res.text[:20]}")
            break
        except Exception as e:
            print(f"Failed {m}: {type(e).__name__} - {e}")

if __name__ == "__main__":
    test()
