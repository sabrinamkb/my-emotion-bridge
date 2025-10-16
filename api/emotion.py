# api/emotion.py

import os
import requests
import time
import json

ASSEMBLYAI_API_KEY = os.environ.get('ASSEMBLYAI_API_KEY')

def handler(request):
    try:
        body = request.json()
        audio_url = body.get('audio_url')

        if not audio_url:
            return {"statusCode": 400, "body": "Missing 'audio_url' from request"}

        if not ASSEMBLYAI_API_KEY:
            return {"statusCode": 500, "body": "AssemblyAI API key not set"}

        transcript_id = submit_audio_for_analysis(audio_url)
        result = get_analysis_result(transcript_id)

        sentiment = "NEUTRAL"
        if result.get('sentiment_analysis_results'):
            sentiment = result['sentiment_analysis_results'][0]['sentiment']

        return {
            "statusCode": 200,
            "body": json.dumps({"detected_emotion": sentiment})
        }

    except Exception as e:
        return {"statusCode": 500, "body": f"Server Error: {str(e)}"}

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
    for _ in range(5):
        response = requests.get(endpoint, headers=headers)
        result = response.json()
        if result['status'] == 'completed': return result
        elif result['status'] == 'error': raise Exception("AssemblyAI analysis failed")
        time.sleep(2)
    raise Exception("Analysis timed out")
