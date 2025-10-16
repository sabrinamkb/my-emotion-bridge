# /api/emotion.py (NEW Real-Time Voice Analysis Version)

import os
import requests
import time
from http.server import BaseHTTPRequestHandler
import json

ASSEMBLYAI_API_KEY = os.environ.get('ASSEMBLYAI_API_KEY')

class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = json.loads(self.rfile.read(content_length))
        
        # We now expect the audio URL from the Custom Tool
        audio_url = body.get('audio_url')

        if not audio_url:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Missing "audio_url" from Ultravox tool')
            return

        try:
            # 1. Submit the audio URL to AssemblyAI
            transcript_id = submit_audio_for_analysis(audio_url)
            
            # 2. Wait for the analysis to complete
            result = get_analysis_result(transcript_id)

            # 3. Get the emotion from the voice analysis
            sentiment = "NEUTRAL"
            if result.get('sentiment_analysis_results'):
                sentiment = result['sentiment_analysis_results'][0]['sentiment']

            # 4. Send the result back to Ultravox
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response_payload = {'detected_emotion': sentiment}
            self.wfile.write(json.dumps(response_payload).encode())

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())
        return

# --- Helper Functions ---

def submit_audio_for_analysis(audio_url):
    endpoint = "https://api.assemblyai.com/v2/transcript"
    headers = {'authorization': ASSEMBLYAI_API_KEY}
    payload = {"audio_url": audio_url, "sentiment_analysis": True}
    response = requests.post(endpoint, json=payload, headers=headers)
    return response.json()['id']

def get_analysis_result(transcript_id):
    endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
    headers = {'authorization': ASSEMBLYAI_API_KEY}
    # Poll for a short period, as this is a real-time interaction
    for _ in range(5): # Try 5 times (10 seconds total)
        response = requests.get(endpoint, headers=headers)
        result = response.json()
        if result['status'] == 'completed':
            return result
        elif result['status
