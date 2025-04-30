from dotenv import load_dotenv
import os

load_dotenv(dotenv_path="key.env")
key = os.getenv("API_KEY")
print("key loaded.")