import os
import sys
import time
from openai import OpenAI
from dotenv import load_dotenv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))

PDF_FILENAME = "BasicCalculus.pdf"
PDF_FILE_PATH_ABSOLUTE = os.path.join(PROJECT_ROOT, "data", PDF_FILENAME)

ASSISTANT_ID_FILE = os.path.join(PROJECT_ROOT, "assistant_id.txt")
ASSISTANT_NAME_FOR_LAB = "Study Q&A Assistant Lab Version"

print(f"--- Debug Info (00_bootstrap.py) ---")
print(f"SCRIPT_DIR: {SCRIPT_DIR}")
print(f"PROJECT_ROOT: {PROJECT_ROOT}")
print(f"Absolute PDF Path attempting to use: {PDF_FILE_PATH_ABSOLUTE}")
print(f"Path to .assistant_id file: {ASSISTANT_ID_FILE}")
print(f"--- End Debug Info ---")

load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, '.env'))
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("ERROR: OPENAI_API_KEY not found in .env file or environment variables.")
    sys.exit(1)
client = OpenAI(api_key=api_key)


def get_or_create_assistant():
    """Creates a new assistant or retrieves an existing one if its ID is saved."""
    if os.path.exists(ASSISTANT_ID_FILE):
        with open(ASSISTANT_ID_FILE, "r") as f:
            assistant_id = f.read().strip()
        if assistant_id:
            print(f"Found existing assistant ID: {assistant_id}.")
            try:
                assistant = client.beta.assistants.retrieve(assistant_id)
                print(f"Successfully retrieved assistant: {assistant.name} (ID: {assistant.id})")
                has_file_search = any(tool.type == "file_search" for tool in assistant.tools)
                if not has_file_search:
                    print(
                        f"Warning: Existing assistant {assistant_id} does not have file_search tool. Attempting to update or consider recreating.")
                return assistant
            except Exception as e:
                print(f"Could not retrieve assistant {assistant_id}. Error: {e}. Creating a new one.")

    print(f"Creating new assistant: '{ASSISTANT_NAME_FOR_LAB}'")
    try:
        assistant = client.beta.assistants.create(
            name=ASSISTANT_NAME_FOR_LAB,
            instructions=(
                "You are a helpful tutor. "
                "Use the knowledge in the attached files to answer questions. "
                "Cite sources where possible."
            ),
            model="gpt-4o-mini",
            tools=[{"type": "file_search"}]
        )
        with open(ASSISTANT_ID_FILE, "w") as f:
            f.write(assistant.id)
        print(f"Created new assistant with ID: {assistant.id}")
        return assistant
    except Exception as e:
        print(f"ERROR: Failed to create assistant. {e}")
        sys.exit(1)


def main():
    if not os.path.exists(PDF_FILE_PATH_ABSOLUTE):
        print(
            f"ERROR: PDF file not found at '{PDF_FILE_PATH_ABSOLUTE}'. Please ensure it exists and the filename in the script ('{PDF_FILENAME}') is correct.")
        sys.exit(1)
    if not os.path.isfile(PDF_FILE_PATH_ABSOLUTE):
        print(f"ERROR: Path '{PDF_FILE_PATH_ABSOLUTE}' exists but is not a file.")
        sys.exit(1)

    assistant = get_or_create_assistant()

    print(f"\nUploading file: {PDF_FILE_PATH_ABSOLUTE}...")
    try:
        with open(PDF_FILE_PATH_ABSOLUTE, "rb") as pdf_file:
            file_object = client.files.create(
                file=pdf_file,
                purpose="assistants"
            )
        print(f"File uploaded successfully. File ID: {file_object.id}, Filename: {file_object.filename}")

        current_vector_store_ids = []
        if assistant.tool_resources and assistant.tool_resources.file_search:
            current_vector_store_ids = assistant.tool_resources.file_search.vector_store_ids or []

        vector_store_id_to_use = None

        if current_vector_store_ids:
            vector_store_id_to_use = current_vector_store_ids[0]
            print(f"Assistant already has vector store(s). Reusing the first one: {vector_store_id_to_use}")

            try:
                vs_file = client.beta.vector_stores.files.create(
                    vector_store_id=vector_store_id_to_use,
                    file_id=file_object.id
                )
                print(
                    f"Added file {file_object.id} to existing vector store {vector_store_id_to_use}. VS File ID: {vs_file.id}")
            except Exception as e:
                print(f"Error adding file {file_object.id} to vector store {vector_store_id_to_use}: {e}")
                print("Proceeding, but the new file might not be in the vector store if this was a critical error.")

        else:
            print(f"Creating a new vector store for assistant {assistant.id}...")
            vector_store = client.beta.vector_stores.create(
                name=f"{assistant.name} Vector Store",
                file_ids=[file_object.id]
            )
            vector_store_id_to_use = vector_store.id
            print(f"New vector store created: {vector_store_id_to_use} and file {file_object.id} added.")


            client.beta.assistants.update(
                assistant_id=assistant.id,
                tool_resources={"file_search": {"vector_store_ids": [vector_store_id_to_use]}}
            )
            print(f"Assistant {assistant.id} updated to use vector store {vector_store_id_to_use}.")

        updated_assistant = client.beta.assistants.retrieve(assistant.id)
        if updated_assistant.tool_resources and \
                updated_assistant.tool_resources.file_search and \
                vector_store_id_to_use in (updated_assistant.tool_resources.file_search.vector_store_ids or []):
            print(f"Confirmed: Assistant {assistant.id} is configured with vector store {vector_store_id_to_use}.")
        else:
            print(
                f"Warning: Assistant {assistant.id} might not be correctly configured with vector store {vector_store_id_to_use}. Please check OpenAI dashboard.")

        print("\nBootstrap complete.")

    except FileNotFoundError:
        print(f"ERROR: Critical - PDF file not found at '{PDF_FILE_PATH_ABSOLUTE}' during file open operation.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: An unexpected error occurred during file operations or assistant update: {e}")
        print("Please check your OpenAI API key, plan, and file access permissions.")
        sys.exit(1)


if __name__ == "__main__":
    main()