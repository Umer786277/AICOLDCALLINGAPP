BASE_URL = 'https://api.vapi.ai'  # Replace with your Vapi API base URL
api_key = '16ca8436-91b6-49e7-b382-60d964aaf646'  # Replace with your Vapi API Authorization token

# utils.py
import requests
from datetime import datetime

def fetch_call_summary(call_id, api_key):
    url = f"{BASE_URL}/call/{call_id}"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        call_data = response.json()
        summary = call_data.get('analysis', {}).get('summary')
        
        return summary
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching call summary: {e}")
        return None

def fetch_call_analytics(call_id, api_key):
    url = f"{BASE_URL}/call/{call_id}"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        call_data = response.json()
        
        started_at = datetime.fromisoformat(call_data.get("startedAt").replace("Z", "+00:00")) if call_data.get("startedAt") else None
        ended_at = datetime.fromisoformat(call_data.get("endedAt").replace("Z", "+00:00")) if call_data.get("endedAt") else None
        
        duration = (ended_at - started_at).total_seconds() if ended_at and started_at else None
        
        analytics = {
            "cost": call_data.get("cost"),
            "duration": duration,
            "status": call_data.get("status"),
        }
        
        return analytics
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching call analytics: {e}")
        return None

def check_lead(summary):
    prompt = f'You are an AI bot made to analyze summaries, your output is limited to an answer of 1 or 0, 1 stands for if the lead is converted and 0 stands for if the lead is not converted. analyze the summary and answer in 1 or 0 {summary} using the summary analyze if the lead is converted or no if converted only reply with 1 if it is not then reply with 0'
    result = execute(prompt)
    return result.strip()
