import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ASSISTANT_NAME = "Study Q&A Assistant"
ASSISTANT_FILE = "assistant_id.txt"

assistant_id = None
if os.path.exists(ASSISTANT_FILE):
    with open(ASSISTANT_FILE, "r") as f:
        assistant_id = f.read().strip()

if assistant_id:
    try:
        assistant = client.beta.assistants.retrieve(assistant_id)
        print(f"Reusing existing assistant: {assistant_id}")
    except Exception:
        assistant = None
        print("Existing assistant not found, creating new one.")
else:
    assistant = None

if not assistant:
    assistant = client.beta.assistants.create(
        name=ASSISTANT_NAME,
        instructions=(
            "You are a helpful tutor. "
            "Use the knowledge in the attached files to answer questions. "
            "Cite sources where possible."
        ),
        model="gpt-4o-mini",
        tools=[{"type": "file_search"}]
    )
    with open(ASSISTANT_FILE, "w") as f:
        f.write(assistant.id)
    print(f"Created new assistant: {assistant.id}")
else:
    print(f"Assistant ready: {assistant.id}") 