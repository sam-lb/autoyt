import os
from dotenv import load_dotenv
from google import genai

load_dotenv(dotenv_path="key.env")
key = os.getenv("API_KEY")
print("key loaded.")

client = genai.Client(api_key=key)

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Hello Gemini, I am testing if my API requests are working. If you are reading this, you are getting a request from my code via the API. Is it working?"
)

print(response.text)