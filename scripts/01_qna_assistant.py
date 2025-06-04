import os
from openai import OpenAI

from dotenv import load_dotenv
from openai.types.beta.threads import Message
from openai.lib.streaming import AssistantEventHandler
from typing_extensions import override

ASSISTANT_ID_FILE = "assistant_id.txt"

client: OpenAI = None


class StudyAssistantEventHandler(AssistantEventHandler):
    def __init__(self):
        super().__init__()
        self.current_response = ""
        self.citations = []

    @override
    def on_text_created(self, text) -> None:
        self.current_response = ""
        self.citations = []

    @override
    def on_text_delta(self, delta, snapshot):
        self.current_response += delta.value

    @override
    def on_message_done(self, message: Message) -> None:

        if message.content:
            for content_block in message.content:
                if content_block.type == 'text' and content_block.text and content_block.text.annotations:
                    for annotation in content_block.text.annotations:
                        if client is None:
                            print("Error: OpenAI client not initialized when processing annotations.")
                            continue

                        text_in_citation_value = annotation.text

                        if annotation.type == 'file_citation':
                            file_id_val = annotation.file_citation.file_id
                            quote_val = getattr(annotation.file_citation, 'quote', None)

                            filename_val = f"File ID: {file_id_val} (name not retrieved)"
                            try:
                                cited_file = client.files.retrieve(file_id_val)
                                filename_val = cited_file.filename
                            except Exception as e_file:
                                print(f"Warning: Could not retrieve filename for {file_id_val}: {e_file}")

                            self.citations.append({
                                "file_id": file_id_val,
                                "filename": filename_val,
                                "quote": quote_val,
                                "text_in_citation": text_in_citation_value
                            })

                        elif annotation.type == 'file_path':
                            file_id_val = annotation.file_path.file_id
                            filename_val = f"File ID: {file_id_val} (name not retrieved)"
                            try:
                                cited_file = client.files.retrieve(file_id_val)
                                filename_val = cited_file.filename
                            except Exception as e_file:
                                print(f"Warning: Could not retrieve filename for {file_id_val}: {e_file}")

                            self.citations.append({
                                "file_id": file_id_val,
                                "filename": filename_val,
                                "text_in_citation": text_in_citation_value
                            })


def main():
    global client
    load_dotenv()
    client = OpenAI()

    if not os.path.exists(ASSISTANT_ID_FILE):
        print(f"Error: Assistant ID file '{ASSISTANT_ID_FILE}' not found. "
              "Please run the bootstrapping script (e.g., 00_bootstrap.py) first.")
        return

    with open(ASSISTANT_ID_FILE, "r") as f:
        assistant_id = f.read().strip()

    if not assistant_id:
        print(f"Error: Assistant ID in '{ASSISTANT_ID_FILE}' is empty. Please check the file or re-run bootstrapping.")
        return

    print(f"Using Assistant ID: {assistant_id}")

    print("Creating a new thread...")
    try:
        thread = client.beta.threads.create()
        print(f"Thread created with ID: {thread.id}")
    except Exception as e:
        print(f"Error creating thread: {e}")
        return

    while True:
        user_question = input("\n🧑 Your question (or type 'quit'): ")
        if user_question.lower() == 'quit':
            break
        if not user_question.strip():
            print("Please enter a question.")
            continue

        try:
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=user_question
            )
        except Exception as e:
            print(f"Error sending message: {e}")
            continue

        event_handler = StudyAssistantEventHandler()
        print("\n🤖 Assistant thinking...\n")
        try:
            with client.beta.threads.runs.stream(
                    thread_id=thread.id,
                    assistant_id=assistant_id,
                    instructions="Please answer the user's question based on the provided documents. Cite your sources clearly.",
                    event_handler=event_handler,
            ) as stream:
                stream.until_done()

        except Exception as e:
            print(f"Error during assistant run: {e}")

            event_handler.current_response = ""
            event_handler.citations = []
            continue


        if event_handler.current_response:
            print("\n🤖 Assistant:", event_handler.current_response)
        else:
            print("\n🤖 Assistant: (No text response received)")

        if event_handler.citations:
            print("\nCitations:")
            for citation in event_handler.citations:
                print(f"  - File: {citation.get('filename', citation.get('file_id', 'Unknown File'))}")
                if citation.get('quote'):
                    print(f"    Reference Text: \"{citation['quote']}\"")

        else:
            print("\nNo citations provided for this response.")

        if any(c.get('file_id') for c in event_handler.citations):
            print("\n✅ Self-check: Answer references at least one chunk ID (file_id) from a document.")
        else:
            if event_handler.current_response:
                print(
                    "\n⚠️ Self-check: No file citations found in the response, or the answer didn't use provided files.")
            else:
                print("\nℹ️ Self-check: No response or citations to check.")

    print("Exiting Q&A session.")


if __name__ == "__main__":
    main()