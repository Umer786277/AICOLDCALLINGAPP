import requests
def create_vapi_call(payload, api_key):
    url = "https://api.vapi.ai/call"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json()