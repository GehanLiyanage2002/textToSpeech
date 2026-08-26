# Text to Speech Web App

A web application that converts text to speech using Azure AI Speech (Text-to-Speech). Users can enter text manually or upload a `.txt` document to download an MP3 audio file.

## Prerequisites

- Python 3.8+
- An Azure AI Speech resource (with Key and Region)

## Setup Instructions

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Azure Credentials:**
   Copy the `.env.example` file to `.env` and fill in your Azure AI Speech credentials:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and set:
   - `AZURE_SPEECH_KEY`: Your Azure Speech resource key.
   - `AZURE_SPEECH_REGION`: Your Azure Speech resource region (e.g., `eastus`).

3. **Run the Application:**
   ```bash
   uvicorn app:app --reload
   ```

4. **Access the Web Interface:**
   Open your browser and navigate to `http://127.0.0.1:8000`.

## Features
- Paste text manually or upload a text file.
- Generates high-quality MP3 audio using Azure AI Speech.
- Directly downloads the converted audio file.
