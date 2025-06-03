# Study Assistant Lab

This project is a mini AI tutor that answers study questions from uploaded PDFs and generates concise revision notes.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and add your OpenAI API key.
3. Place your study PDFs in the `data/` directory (e.g., `data/calculus_basics.pdf`).

## Usage

### Part 1: Q&A Assistant from PDFs

- Run the bootstrap script to create the assistant:
  ```bash
  python scripts/00_bootstrap.py
  ```
- Run the Q&A assistant to ask questions:
  ```bash
  python scripts/01_qna_assistant.py
  ```

### Part 2: Generate 10 Exam Notes

- Run the notes generator:
  ```bash
  python scripts/02_generate_notes.py
  ```
- The notes will be saved to `exam_notes.json`.

### Cleanup

- Run the cleanup script to remove resources:
  ```bash
  python scripts/99_cleanup.py
  ```

## Testing (Optional)

- Run tests with pytest:
  ```bash
  pytest tests/
  ```
