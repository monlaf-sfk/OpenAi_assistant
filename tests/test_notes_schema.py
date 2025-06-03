import json
import os
import pytest
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional

class Note(BaseModel):
    id: int = Field(..., ge=1, le=10, description="Unique note ID, 1-10.")
    heading: str = Field(..., min_length=3, example="Mean Value Theorem", description="Concise heading.")
    summary: str = Field(..., min_length=10, max_length=150, description="Brief summary, max 150 chars.")
    page_ref: Optional[int] = Field(None, ge=1, description="Page number in source PDF if applicable.")


class NotesContainer(BaseModel):
    notes: List[Note]


# --- Test Function ---
def test_exam_notes_file_schema_and_content():

    exam_notes_file_path = "/Users/rasulkerimzhanov/Desktop/nfac homeworks/1.1 Ai Homework/scripts/exam_notes.json"
    print(f"Exam notes file path: {exam_notes_file_path}")
    assert os.path.exists(exam_notes_file_path), \
        f"{exam_notes_file_path} not found. Run 02_generate_notes.py first to create it."

    with open(exam_notes_file_path, "r") as f:
        try:
            data_from_file = json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"Failed to decode JSON from {exam_notes_file_path}: {e}")

    try:
        notes_container_obj = NotesContainer(**data_from_file)
    except ValidationError as e:
        pytest.fail(
            f"Schema validation failed for {exam_notes_file_path}. The file content does not match the expected NotesContainer structure (e.g., missing 'notes' key or invalid note items):\n{e}")

    actual_notes_list = notes_container_obj.notes
    assert isinstance(actual_notes_list, list), "The 'notes' field in the JSON should be a list."

    if len(actual_notes_list) != 10:
        pytest.warn(UserWarning(f"Expected 10 notes, but found {len(actual_notes_list)} in {exam_notes_file_path}."))
    else:
        print(f"Found exactly {len(actual_notes_list)} notes as expected.")

    assert len(actual_notes_list) > 0, "The 'notes' list should not be empty if checks are to proceed."

    for i, item_data in enumerate(actual_notes_list):
        try:
            note_instance = Note(
                **item_data.model_dump())
            assert note_instance.id == i + 1, f"Note ID should be sequential and start from 1. Found ID {note_instance.id} for note supposedly at index {i}."
            assert 1 <= note_instance.id <= 10, f"Note ID {note_instance.id} is out of range (1-10)."
            assert len(note_instance.summary) <= 150, f"Summary for note ID {note_instance.id} exceeds 150 characters."

        except ValidationError as e:
            pytest.fail(f"Invalid note structure for item at index {i} (ID: {item_data.get('id', 'Unknown')}): {e}")

    print(f"Successfully validated schema and content of {exam_notes_file_path}")


