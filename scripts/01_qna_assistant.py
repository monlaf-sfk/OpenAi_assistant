import os
from openai import OpenAI

from dotenv import load_dotenv
from openai.types.beta.threads import Message

ASSISTANT_ID_FILE = "assistant_id.txt"

from openai.lib.streaming import AssistantEventHandler
from typing_extensions import override


class StudyAssistantEventHandler(AssistantEventHandler):
    def __init__(self):
        super().__init__()
        self.current_response = ""
        self.citations = []



    @override
    def on_text_delta(self, delta, snapshot):
        self.current_response += delta.value



    @override
    def on_message_done(self, message: Message) -> None:
        self.citations = []
        if message.content:
            for content_block in message.content:
                if content_block.type == 'text' and content_block.text and content_block.text.annotations:
                    for annotation in content_block.text.annotations:
                        if annotation.type == 'file_citation':
                            cited_file = client.files.retrieve(annotation.file_citation.file_id)
                            self.citations.append({
                                "file_id": annotation.file_citation.file_id,
                                "filename": cited_file.filename,
                                "quote": annotation.file_citation.quote,
                                "text_in_citation": annotation.text
                            })
                        elif annotation.type == 'file_path':
                            cited_file = client.files.retrieve(annotation.file_path.file_id)
                            self.citations.append({
                                "file_id": annotation.file_path.file_id,
                                "filename": cited_file.filename,
                                "text_in_citation": annotation.text
                            })


def main():
    global client
    load_dotenv()
    client = OpenAI()

    if not os.path.exists(ASSISTANT_ID_FILE):
        print(f"Error: Assistant ID file '{ASSISTANT_ID_FILE}' not found. Please run 00_bootstrap.py first.")
        return

    with open(ASSISTANT_ID_FILE, "r") as f:
        assistant_id = f.read().strip()

    print(f"Using Assistant ID: {assistant_id}")

    print("Creating a new thread...")
    thread = client.beta.threads.create()
    print(f"Thread created with ID: {thread.id}")

    while True:
        user_question = input("\n🧑 Your question (or type 'quit'): ")
        if user_question.lower() == 'quit':
            break

        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_question
        )

        event_handler = StudyAssistantEventHandler()
        print("\n🤖 Assistant thinking...\n")
        with client.beta.threads.runs.stream(
                thread_id=thread.id,
                assistant_id=assistant_id,
                instructions="Please answer the user's question based on the provided documents. Cite your sources clearly.",
                event_handler=event_handler,
        ) as stream:
            stream.until_done()

        print("\n🤖 Assistant:", event_handler.current_response)
        if event_handler.citations:
            print("\nCitations:")
            for citation in event_handler.citations:
                print(f"  - File: {citation.get('filename', citation['file_id'])}")
                if 'quote' in citation and citation['quote']:
                    print(f"    Reference Text: \"{citation['quote']}\"")

            if any(c.get('file_id') for c in event_handler.citations):
                print("\n✅ Self-check: Answer references at least one chunk ID (file_id) from the PDF.")
            else:
                print("\n⚠️ Self-check: No file citations found in the response.")
        else:
            print("\nNo citations provided for this response.")

        event_handler.current_response = ""
        event_handler.citations = []

    print("Exiting Q&A session.")


if __name__ == "__main__":
    main()