# /api/emotion.py (NEW Custom Tool Version)

import os
import requests
from http.server import BaseHTTPRequestHandler
import json

ASSEMBLYAI_API_KEY = os.environ.get('ASSEMBLYAI_API_KEY')
# We don't need the Ultravox key anymore, as we are responding directly to the tool call.

class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        # 1. Read the text sent from the Ultravox Custom Tool
        content_length = int(self.headers['Content-Length'])
        body = json.loads(self.rfile.read(content_length))
        
        user_text = body.get('text') # Expecting a JSON with a "text" field

        if not user_text:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Missing "text" field in the request')
            return

        try:
            # 2. Send the text to AssemblyAI's sentiment analysis
            sentiment = get_sentiment_from_text(user_text)

            # 3. Send the result DIRECTLY back to the Ultravox tool
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # This is the response Ultravox will receive and use
            response_payload = {'detected_emotion': sentiment} 
            self.wfile.write(json.dumps(response_payload).encode())

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())
        return

def get_sentiment_from_text(text_to_analyze):
    """Submits text directly to AssemblyAI for sentiment analysis."""
    endpoint = "https://api.assemblyai.com/v2/transcript"
    headers = {'authorization': ASSEMBLYAI_API_KEY}
    
    # We create a "mock" transcript with the text we already have
    payload = {
        "text": text_to_analyze,
        "sentiment_analysis": True
    }
    response = requests.post(endpoint, json=payload, headers=headers)
    result = response.json()
    
    # The result is immediate since we provided the text directly
    if result.get('sentiment_analysis_results'):
        return result['sentiment_analysis_results'][0]['sentiment']
    return "NEUTRAL"
