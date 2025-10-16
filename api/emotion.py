# /api/emotion.py

import os
import requests
import time
from http.server import BaseHTTPRequestHandler
import json

# We will get these from Vercel's "Environment Variables"
ASSEMBLYAI_API_KEY = os.environ.get('ASSEMBLYAI_API_KEY')
ULTRAVOX_API_KEY = os.environ.get('ULTRAVOX_API_KEY')

class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        # 1. Read the data sent from Ultravox
        content_length = int(self.headers['Content-Length'])
        body = json.loads(self.rfile.read(content_length))

        audio_url = body.get('audio_url')
        conversation_id = body.get('conversation_id')

        if not audio_url or not conversation_id:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Missing data from Ultravox')
            return

        try:
            # 2. Send audio to AssemblyAI and get the result
            transcript_id = submit_audio_for_analysis(audio_url)
            result = get_analysis_result(transcript_id)

            # 3. Find the overall emotion (sentiment)
            sentiment = "NEUTRAL"
            if result.get('sentiment_analysis_results'):
                sentiment = result['sentiment_analysis_results'][0]['sentiment']

            # 4. Send the result back to Ultravox
            update_ultravox_context(conversation_id, sentiment)

            # 5. Send a success response
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'success', 'detected_emotion': sentiment}).encode())

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())
        return

# --- Helper Functions (these are the same as before) ---

def submit_audio_for_analysis(audio_url):
    endpoint = "https://api.assemblyai.com/v2/transcript"
    headers = {'authorization': ASSEMBLYAI_API_KEY}
    payload = {"audio_url": audio_url, "sentiment_analysis": True}
    response = requests.post(endpoint, json=payload, headers=headers)
    return response.json()['id']

def get_analysis_result(transcript_id):
    endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
    headers = {'authorization': ASSEMBLYAI_API_KEY}
    while True:
        response = requests.get(endpoint, headers=headers)
        result = response.json()
        if result['status'] == 'completed':
            return result
        elif result['status'] == 'error':
            raise Exception("AssemblyAI analysis failed")
        time.sleep(2)

def update_ultravox_context(conversation_id, emotion):
    url = f"https://api.ultravox.ai/v1/conversations/{conversation_id}/context"
    headers = {'Authorization': f'Bearer {ULTRAVOX_API_KEY}', 'Content-Type': 'application/json'}
    payload = {"variables": {"customer_emotion": emotion.lower()}}
    requests.patch(url, json=payload, headers=headers)