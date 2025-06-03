import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ASSISTANT_FILE = "assistant_id.txt"

if os.path.exists(ASSISTANT_FILE):
    with open(ASSISTANT_FILE, "r") as f:
        assistant_id = f.read().strip()
    try:
        client.beta.assistants.delete(assistant_id)
        print(f"Deleted assistant: {assistant_id}")
    except Exception as e:
        print(f"Error deleting assistant: {e}")
    os.remove(ASSISTANT_FILE)
    print("Removed assistant_id.txt")
else:
    print("No assistant_id.txt found. Nothing to clean up.") 