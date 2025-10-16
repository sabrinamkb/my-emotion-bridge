# /api/emotion.py (NEW DEBUGGING Version)

import os
import requests
import time
from http.server import BaseHTTPRequestHandler
import json

ASSEMBLYAI_API_KEY = os.environ.get('ASSEMBLYAI_API_KEY')

class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        # BREADCRUMB 1: Check if the function starts
        print("[DEBUG] Function execution started.")

        try:
            content_length = int(self.headers['Content-Length'])
            body = json.loads(self.rfile.read(content_length))

            # BREADCRUMB 2: Check what data we received from Ultravox
            print(f"[DEBUG] Received data from Ultravox: {json.dumps(body)}")

            audio_url = body.get('audio_url')

            if not audio_url:
                print("[ERROR] 'audio_url' was not found in the received data!")
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Missing "audio_url" from Ultravox tool')
                return

            # BREADCRUMB 3: Confirm we found the audio URL
            print(f"[DEBUG] Found audio_url: {audio_url}")

            # BREADCRUMB 4: Check if the API key is loaded
            if not ASSEMBLYAI_API_KEY:
                print("[FATAL ERROR] ASSEMBLYAI_API_KEY is missing from environment variables!")
                raise Exception("Server configuration error: AssemblyAI API key not set.")

            print("[DEBUG] AssemblyAI API Key is present. Submitting for analysis...")

            transcript_id = submit_audio_for_analysis(audio_url)
            print(f"[DEBUG] Submitted to AssemblyAI. Transcript ID: {transcript_id}")

            result = get_analysis_result(transcript_id)
            print("[DEBUG] Analysis complete from AssemblyAI.")

            sentiment = "NEUTRAL"
            if result.get('sentiment_analysis_results'):
                sentiment = result['sentiment_analysis_results'][0]['sentiment']
            print(f"[DEBUG] Detected sentiment: {sentiment}")

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response_payload = {'detected_emotion': sentiment}
            self.wfile.write(json.dumps(response_payload).encode())
            print("[DEBUG] Successfully sent response back to Ultravox.")

        except Exception as e:
            # BREADCRUMB 5: This will print the EXACT error if the code crashes!
            print(f"[FATAL CRASH] An exception occurred: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())
        return

# --- Helper Functions (unchanged) ---
def submit_audio_for_analysis(audio_url):
    endpoint = "https://api.assemblyai.com/v2/transcript"
    headers = {'authorization': ASSEMBLYAI_API_KEY}
    payload = {"audio_url": audio_url, "sentiment_analysis": True}
    response = requests.post(endpoint, json=payload, headers=headers)
    return response.json()['id']

def get_analysis_result(transcript_id):
    endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
    headers = {'authorization': ASSEMBLYAI_API_KEY}
    for _ in range(5):
        response = requests.get(endpoint, headers=headers)
        result = response.json()
        if result['status'] == 'completed': return result
        elif result['status'] == 'error': raise Exception("AssemblyAI analysis failed")
        time.sleep(2)
    raise Exception("Analysis timed out")
