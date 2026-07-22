# FUME Client Intelligence Assistant

A lightweight GenAI prototype that turns a coach-client transcript into a structured, evidence-grounded weekly client intelligence report for human review.

## Overview

This project is built as a Streamlit application that:

- accepts a transcript as pasted text
- sends it to an LLM for structured analysis
- extracts weekly client intelligence such as adherence, barriers, risks, and recommended action
- returns evidence-backed output in a normalized JSON-like structure
- saves the latest analysis to the `outputs/` folder

## Purpose

The goal of this app is to reduce manual effort for coaches by summarizing transcript content into a concise, reviewable format rather than forcing a reviewer to read the full conversation.

## Features

- Transcript input via Streamlit UI
- Structured response model for client intelligence
- Evidence grounding for extracted metrics and claims
- Risk flag and action-item extraction
- Safe fallback behavior when data is missing
- Output persistence in `outputs/latest_analysis.json`

## Tech Stack

- Python
- Streamlit
- OpenAI Python SDK
- Pydantic
- python-dotenv

## Project Structure

```text
.
├── app.py                  # Main Streamlit application
├── PRD.md                 # Product requirements document
├── requirements.txt       # Python dependencies
└── .env                   # Local environment variables (not committed)
```

## Setup

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with one of the following keys:

```env
GROQ_API_KEY=your_groq_key_here
# or
OPENAI_API_KEY=your_openai_key_here
```

Optional model override:

```env
GROQ_MODEL=llama-3.3-70b-versatile
```

## Run the App

From the project root:

```bash
streamlit run app.py
```

Then open the local URL shown in the terminal.

## How It Works

1. The user pastes a transcript into the Streamlit interface.
2. The app builds a prompt and sends it to the configured model.
3. The model returns structured JSON.
4. The response is normalized into a strict schema.
5. The final structured report is displayed in the UI and saved to `outputs/latest_analysis.json`.

## Notes

- This is a prototype and is intentionally not a production-grade clinical or operational system.
- The application is designed for human review and evidence-backed interpretation, not autonomous decision-making.
- If no API key is configured, the app will show an error and cannot generate analysis.

## License

This project is for educational and prototype use.
