# api/emotion.py (Vercel + Ultravox compatible)
import os
import requests
import json

ASSEMBLYAI_API_KEY = os.environ.get('ASSEMBLYAI_API_KEY')

# Handler called by Ultravox
def handler(request):
    try:
        body = request.json()
        audio_url = body.get('audio_url')

        if not audio_url:
            return {"statusCode": 400, "body": "Missing 'audio_url'"}

        if not ASSEMBLYAI_API_KEY:
            return {"statusCode": 500, "body": "AssemblyAI API key not set"}

        # Submit audio to AssemblyAI
        transcript_id = submit_audio_for_analysis(audio_url)

        # Try to get result once (avoid long polling in serverless)
        result = check_analysis_result(transcript_id)
        if not result:
            # Still processing
            return {"statusCode": 200, "body": json.dumps({"status": "processing", "transcript_id": transcript_id})}

        sentiment = "NEUTRAL"
        if result.get('sentiment_analysis_results'):
            sentiment = result['sentiment_analysis_results'][0]['sentiment']

        return {"statusCode": 200, "body": json.dumps({"status": "done", "detected_emotion": sentiment})}

    except Exception as e:
        return {"statusCode": 500, "body": f"Server Error: {str(e)}"}

# --- Helper functions ---
def submit_audio_for_analysis(audio_url):
    endpoint = "https://api.assemblyai.com/v2/transcript"
    headers = {'authorization': ASSEMBLYAI_API_KEY}
    payload = {"audio_url": audio_url, "sentiment_analysis": True}
    response = requests.post(endpoint, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()['id']

def check_analysis_result(transcript_id):
    endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
    headers = {'authorization': ASSEMBLYAI_API_KEY}
    response = requests.get(endpoint, headers=headers)
    response.raise_for_status()
    result = response.json()
    if result['status'] == 'completed':
        return result
    elif result['status'] == 'error':
        raise Exception("AssemblyAI analysis failed")
    else:
        # Still processing
        return None
