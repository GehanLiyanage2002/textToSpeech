import os
import uuid
import asyncio
import tempfile
import azure.cognitiveservices.speech as speechsdk
from fastapi import FastAPI, Form, File, UploadFile, Request, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

templates = Jinja2Templates(directory="templates")

SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")

import html

def synthesize_speech(text: str, output_filepath: str, voice_param: str, speed: str):
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    # Output format set to MP3
    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3)
    
    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_filepath)
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    
    # Parse voice and style
    parts = voice_param.split("|")
    voice = parts[0]
    style = parts[1] if len(parts) > 1 else "none"
    
    # Map speed to prosody rate
    speed_map = {
        "slow": "-25%",
        "medium": "0%",
        "fast": "+30%",
        "very_fast": "+50%"
    }
    rate = speed_map.get(speed, "0%")
    
    # Safely escape text for XML/SSML
    escaped_text = html.escape(text)
    
    # Wrap text with style if requested
    if style != "none":
        inner_ssml = f'<mstts:express-as style="{style}">\n            <prosody rate="{rate}">\n                {escaped_text}\n            </prosody>\n        </mstts:express-as>'
    else:
        inner_ssml = f'<prosody rate="{rate}">\n            {escaped_text}\n        </prosody>'
    
    # Create SSML string to control voice, style, and speed
    ssml = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="en-US">
    <voice name="{voice}">
        {inner_ssml}
    </voice>
</speak>"""
    
    result = speech_synthesizer.speak_ssml_async(ssml).get()
    
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return True, None
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        error_msg = f"Speech synthesis canceled: {cancellation_details.reason}"
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            error_msg += f". Error details: {cancellation_details.error_details}"
        return False, error_msg

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/convert")
async def convert_to_speech(
    text: str = Form(None), 
    file: UploadFile = File(None),
    voice: str = Form("en-US-JennyNeural|chat"),
    speed: str = Form("medium")
):
    if not SPEECH_KEY or not SPEECH_REGION:
        raise HTTPException(status_code=500, detail="Azure Speech configuration is missing. Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION in .env")

    content = ""
    if file and file.filename:
        try:
            content_bytes = await file.read()
            content = content_bytes.decode("utf-8")
        except Exception as e:
            raise HTTPException(status_code=400, detail="Failed to read file. Please ensure it's a valid text file.")
    elif text:
        content = text
    
    if not content.strip():
        raise HTTPException(status_code=400, detail="No text provided.")

    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join(tempfile.gettempdir(), filename)

    success, error_msg = await asyncio.to_thread(synthesize_speech, content, filepath, voice, speed)

    if not success:
        raise HTTPException(status_code=500, detail=error_msg)

    return FileResponse(filepath, media_type="audio/mpeg", filename="output.mp3")
