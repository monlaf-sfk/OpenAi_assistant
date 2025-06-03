import json
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional


class Note(BaseModel):
    id: int = Field(..., ge=1, le=10, description="Unique note ID between 1 and 10.")
    heading: str = Field(..., example="Mean Value Theorem", description="A concise heading for the note.")
    summary: str = Field(..., max_length=150, description="A brief summary, max 150 characters.")
    page_ref: Optional[int] = Field(None, description="Page number in source PDF, if applicable.")


class NotesList(BaseModel):
    notes: List[Note]


def generate_exam_notes():
    load_dotenv()
    client = OpenAI()

    system_prompt = (
        "You are a study summarizer. Your task is to extract key concepts "
        "from the provided study material context (which will be implicitly available to you if relevant documents were processed). "
        "Return exactly 10 unique, bite-sized revision notes that will help prepare for an exam on this material. "
        "Each note should have an 'id' from 1 to 10, a 'heading', a 'summary' (max 150 chars), "
        "and an optional 'page_ref' if a specific page can be cited. "
        "Respond *only* with a single valid JSON object that strictly matches the following schema: "
        "{'notes': [{'id': int, 'heading': str, 'summary': str, 'page_ref': int | null}, ...]}"
    )

    user_context_message = (
        "The study material is about the basics of Calculus, including topics like "
        "limits, derivatives, the definition of an integral (definite and indefinite), "
        "and fundamental theorems like the Mean Value Theorem and the Fundamental Theorem of Calculus. "
        "Please generate notes based on these core calculus concepts."
    )

    print("Generating exam notes...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_context_message}
            ],
            response_format={"type": "json_object"}
        )

        raw_content = response.choices[0].message.content

        data = json.loads(raw_content)

        validated_notes = NotesList(**data)

        print("\nGenerated Exam Notes (Validated):")
        for note in validated_notes.notes:
            print(f"  ID: {note.id}")
            print(f"  Heading: {note.heading}")
            print(f"  Summary: {note.summary}")
            if note.page_ref is not None:
                print(f"  Page Ref: {note.page_ref}")
            print("-" * 20)

        output_filename = "exam_notes.json"
        with open(output_filename, "w") as f:
            json.dump(data, f, indent=2)
        print(f"\nNotes saved to {output_filename}")

        if len(validated_notes.notes) == 10:
            print(f"\n✅ Successfully generated exactly {len(validated_notes.notes)} notes.")
        else:
            print(f"\n⚠️ Warning: Generated {len(validated_notes.notes)} notes, but expected 10.")


    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON from API response. Details: {e}")
        print(f"Raw response was: {raw_content if 'raw_content' in locals() else 'not available'}")
    except ValidationError as e:
        print(f"Error: API response did not match the Pydantic schema. Details:\n{e}")
        print(f"Raw response was: {raw_content if 'raw_content' in locals() else 'not available'}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    generate_exam_notes()