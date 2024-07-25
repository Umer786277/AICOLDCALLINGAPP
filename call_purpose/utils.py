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




import os, re
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

groq_api_key  = "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"

client = Groq(api_key="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")
model = "llama3-8b-8192"








 

def summarize_text(text, chunk_size=1000):
    summary = ""
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        combined_text = summary + " " + chunk     
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": f"Summarize the following text to create a concise summary about the brand. The summary must include key details such as name, address, phone number, email, and unique selling points. If any details are not found, write 'not provided'. Format the summary in a list. For example: \n\nName: Scents N Stories\nAddress: Lahore\nPhone Number: +92 311 100 7862\nEmail: test@gmail.com\n\nUnique Selling Points: [Unique points about the brand]\n\nText to summarize: {combined_text}",
                    }
                ],
                model="llama3-8b-8192",
            )
            summary = chat_completion.choices[0].message.content.strip()
        except Exception as e:
            summary = f"Error in summarization: {str(e)}"
            break  # Exit the loop on error to avoid further calls with the same issue
    return summary

# Helper function to calculate SEO score using Groq API
def calculate_seo_score(meta, slug):
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"Calculate the SEO score based on the following meta and slug information:\nMeta: {meta}\nSlug: {slug}, Just Provide me the Scores with headings",
                }
            ],
            model=model,
        )
        seo_score = chat_completion.choices[0].message.content.strip()
    except Exception as e:
        seo_score = f"Error in SEO score calculation: {str(e)}"
    return seo_score

# Helper function to get technology stacks using Groq API
def get_tech_stacks(url):
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"Identify the technology stacks used by the website at the following URL: {url}, Just give me the names of Technology stacks.",
                }
            ],
            model=model,
        )
        tech_stacks = chat_completion.choices[0].message.content.strip().split('\n')
    except Exception as e:
        tech_stacks = [f"Error in fetching technology stacks: {str(e)}"]
    
    return tech_stacks

# Helper function to get traffic analysis using Groq API
def get_traffic_analysis(url):
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"Provide a traffic analysis for the website at the following URL: {url}. Please provide me concise ad accurate traffic analysis",
                }
            ],
            model=model,
        )
        traffic_analysis = chat_completion.choices[0].message.content.strip()
    except Exception as e:
        traffic_analysis = f"Error in fetching traffic analysis: {str(e)}"
    return traffic_analysis

# Helper function to extract meta and slug from HTML
def extract_meta_and_slug(html_content):
    # Extract meta description
    meta_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
    meta = meta_match.group(1) if meta_match else 'No meta description available'
    
    # Extract slug
    slug_match = re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
    slug = slug_match.group(1).split('/')[-1] if slug_match else 'No slug available'
    
    return meta, slug

from bs4 import BeautifulSoup


def extract_meta_and_slug_soup(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract meta description
    meta_tag = soup.find('meta', attrs={'name': 'description'})
    if meta_tag:
        meta = meta_tag['content']
    else:
        meta = 'No meta description available'
        print("Meta tag not found")

    # Extract slug
    canonical_link = soup.find('link', rel='canonical')
    if canonical_link:
        slug = canonical_link['href'].split('/')[-1]
    else:
        slug = 'No slug available'
        print("Canonical link not found")
    
    return meta, slug

# Function to process website content
def process_website_content(url, html_content):
    print(html_content)
    meta, slug = extract_meta_and_slug_soup(html_content)
    print('hehe=>new',meta, slug)
    # Summarize HTML content
    brand_summary = summarize_text(html_content)
    print("Brand Summary:       ",brand_summary)
    tech_stacks = get_tech_stacks(url)
    # Calculate SEO score
    seo_score = calculate_seo_score(meta, slug)
    
    # Provide traffic analysis
    traffic_analysis = get_traffic_analysis(url)
    
    return {
        "brand_summary": brand_summary,
        "seo_score": seo_score,
        "tech_stacks": tech_stacks,
        "traffic_analysis": traffic_analysis
    }

import re

def parse_brand_summary(brand_summary):
    # Using regular expressions to find the required fields
    name_match = re.search(r'\*\*Name:\*\*\s*(.*)', brand_summary)
    phone_number_match = re.search(r'\*\*Phone Number:\*\*\s*(.*)', brand_summary)
    email_match = re.search(r'\*\*Email:\*\*\s*(.*)', brand_summary)
    address_match = re.search(r'\*\*Address:\*\*\s*(.*)', brand_summary)

    return {
        'Name': name_match.group(1) if name_match else None,
        'Phone Number': phone_number_match.group(1) if phone_number_match else None,
        'Email': email_match.group(1) if email_match else None,
        'Address': address_match.group(1) if address_match else None,
    }


# New function to get the brand category
def get_brand_category(brand_summary):
    parsed_data = parse_brand_summary(brand_summary)
    brand_name = parsed_data.get("Name")
    if not brand_name:
        return "Brand name not found in summary"
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"Based on the following brand summary {parsed_data},  determine the single-word category it deals in (e.g., shoes, clothing, electronics, etc.): {brand_name}",
                }
            ],
            model=model,
        )
        category = chat_completion.choices[0].message.content.strip()
    except Exception as e:
        category = f"Error in fetching brand category: {str(e)}"
    
    return category