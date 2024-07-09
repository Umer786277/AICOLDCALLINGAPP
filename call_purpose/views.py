import os
import json
import logging
from dotenv import load_dotenv
import base64
from datetime import datetime
import requests
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status, generics
from .models import Lead, CustomUser, Company, Call, CallSummary
from .serializers import CallPurposeSerializer, CompanySerializer
from .forms import CallForm, CallPurposeForm
from firecrawl import FirecrawlApp
from groq import Groq


google_api_key = os.getenv('GOOGLE_API_KEY')
search_engine_id = os.getenv('SEARCH_ENGINE_ID')
firecrawl_api_key = os.getenv('FIRECRAWL_API_KEY')
builtwith_api_key = os.getenv('BUILTWITH_API_KEY')
backlink_api_key = os.getenv('BACKLINK_API_KEY')
similarweb_api_key = os.getenv('SIMILARWEB_API_KEY')
groq_api_key  ="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"
moz_access_id = os.getenv('MOZ_ACCESS_ID')
moz_secret_key = os.getenv('MOZ_SECRET_KEY')



CustomUser = get_user_model()
logger = logging.getLogger(__name__)


# Your Vapi API Authorization token
AUTH_TOKEN = '16ca8436-91b6-49e7-b382-60d964aaf646'
BASE_URL = 'https://api.vapi.ai'
HEADERS = {
    'Authorization': f'Bearer {AUTH_TOKEN}',
    'Content-Type': 'application/json',
}

# Your LLM API details (e.g., GROQ Llama 80B)
LLM_API_KEY = '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'
LLM_BASE_URL = 'https://api.groq.com/openai/v1/chat/completions'
LLM_HEADERS = {
    'Authorization': f'Bearer {LLM_API_KEY}',
    'Content-Type': 'application/json',
}

def index(request):

    return render(request,'dashboard/dashboard-3.html')


def signup_page(request):
    return render(request, 'auth/register-2.html')




def signup(request):
    if request.method == 'POST':
        if request.POST.get('password1') == request.POST.get('password2'):
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password1')

            try:
                if CustomUser.objects.get(username=username):
                    messages.error(request, "Username already taken.", extra_tags='alert')
            except ObjectDoesNotExist:
                # Create a new CustomUser instance instead of User.objects.create_user
                new_user = CustomUser.objects.create_user(username=username, email=email, password=password)
                new_user.is_active = True
                new_user.save()

                # Call method to create user folders and save initial data
                new_user.create_user_folders()
                initial_data = {'username': new_user.username, 'email': new_user.email}
                new_user.save_user_data_to_json(initial_data)

                messages.success(request, "Your information has been submitted.", extra_tags='alert')
                return redirect('signin')
        else:
            messages.error(request, "Passwords do not match.", extra_tags='alert')

    return render(request, 'auth/register-2.html')





def signin(request):
    if request.user.is_authenticated:
        messages.warning(request, "You are already logged in")
        return redirect('/')
    else:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            print("**********", password)
            logger.debug("Attempting to authenticate user with username: %s", username)
            user = authenticate(request, username=username, password=password)  # Check password
            logger.debug("Authentication result: %s", user)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are logged in as {username}")
                return redirect('/')
            else:
                messages.error(request, "Username or Password is Incorrect")

    return render(request, 'auth/login-2.html')



@login_required
def logout_request(request):
	logout(request)
	messages.info(request, "You have successfully logged out.") 
	return redirect("/")







def execute(prompt):
    llm_data = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    
    response = requests.post(LLM_BASE_URL, headers=LLM_HEADERS, json=llm_data)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']

def create_a_purpose(lead):
    prompt = f'{lead} this is the details of a customer, TechRealm sells seo,digital marketing,web development and more. you need to create a prompt for a marketing agent to tell him how to talk to the client what to present and most importantly what to ask the client about.'
    purpose = execute(prompt)
    return purpose

def check_lead(summary):
    prompt = f'You are an AI bot made to analyze summaries, your output is limited to an answer of 1 or 0, 1 stands for if the lead is converted and 0 stands for if the lead is not converted. analyze the summary and answer in 1 or 0 {summary} using the summary analyze if the lead is converted or no if converted only reply with 1 if it is not then reply with 0'
    result = execute(prompt)
    return result.strip()




@csrf_exempt
def add_lead(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        contact_information = request.POST.get('contact_info')
        industry = request.POST.get('industry')
        location = request.POST.get('location')

        if name and contact_information and industry and location:
            lead = Lead.objects.create(
                name=name,
                contact_information=contact_information,
                industry=industry,
                location=location
            )
            return JsonResponse({'id': lead.id, 'status': 'Lead added'}, status=201)
        return JsonResponse({'error': 'Invalid input'}, status=400)
    return HttpResponse(status=405)

@csrf_exempt
def get_or_update_lead(request, id):
    try:
        lead = Lead.objects.get(id=id)
        
        if request.method == 'PUT':
            data = json.loads(request.body)
            name = data.get('name')
            contact_info = data.get('contact_info')
            industry = data.get('industry')
            location = data.get('location')
            notes = data.get('notes')
            if name:
                lead.name = name
            if contact_info:
                lead.contact_information = contact_info
            if industry:
                lead.industry = industry
            if location:
                lead.location = location
            if notes:
                lead.notes = notes

            lead.save()
            return JsonResponse({'id': lead.id, 'name': lead.name, 'industry': lead.industry, 'status': 'Lead updated'})

        elif request.method == 'GET':
            # Handle GET request to retrieve lead details
            lead_data = {
                'id': lead.id,
                'name': lead.name,
                'contact_info': lead.contact_information,
                'industry': lead.industry,
                'location': lead.location,
                'notes': lead.notes
            }
            return JsonResponse(lead_data)

        else:
            return HttpResponse(status=405)  # Method Not Allowed for other methods
    
    except Lead.DoesNotExist:
        return JsonResponse({'error': 'Lead not found'}, status=404)

@csrf_exempt
def find_leads(request):
    query = request.GET.get('query', '')
    
    leads = Lead.objects.filter(
        Q(industry__icontains=query) |
        Q(location__icontains=query) |
        Q(name__icontains=query) |
        Q(contact_information__icontains=query)
    )

    leads_data = [{
        'id': lead.id,
        'name': lead.name,
        'contact_info': lead.contact_information,
        'industry': lead.industry,
        'location': lead.location,
        'notes': lead.notes
    } for lead in leads]
    
    return JsonResponse(leads_data, safe=False)


@csrf_exempt
def add_notes(request, id):
    try:
        lead = Lead.objects.get(id=id)
        if request.method == 'POST':
            notes = request.POST.get('notes')
            if notes:
                lead.notes = lead.notes + '\n' + notes if lead.notes else notes
                lead.save()
                return JsonResponse({'id': lead.id, 'status': 'Notes added'})
            return JsonResponse({'error': 'No notes provided'}, status=400)
        return HttpResponse(status=405)
    except Lead.DoesNotExist:
        return JsonResponse({'error': 'Lead not found'}, status=404)

print(f"Groq API Key: {groq_api_key}")

client = Groq(api_key=groq_api_key)

def summarize_text(text):
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"Summarize the following text and generate a comprehensive summary about the brand, including key details and unique selling points: {text}",
                }
            ],
            model="llama3-8b-8192",
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        return f"Error in summarization: {str(e)}"


def generate_custom_suggestions(email_contents):
    suggestions = []

    for content in email_contents:
        link = content['link']
        summary = content['summary']
        technology_stacks = content['technology stacks']
        backlink_count = content['backlink_count']
        traffic_visits = content['traffic_visits']

        # Generate detailed suggestions based on the data
        suggestion = f"Consider leveraging SEO analytics for {link}. "
        
        if backlink_count > 0:
            suggestion += f"They have a significant backlink profile with {backlink_count} backlinks. "
        else:
            suggestion += "They currently have no significant backlinks. "
        
        if traffic_visits > 0:
            suggestion += f"The site receives {traffic_visits} visits per month, indicating a healthy level of traffic. "
        else:
            suggestion += "The site does not appear to have significant traffic data available. "

        if technology_stacks:
            tech_summary = ', '.join([tech['Name'] for tech in technology_stacks])
            suggestion += f"The site uses the following technologies: {tech_summary}. "
        else:
            suggestion += "No technology stack information is available. "

        suggestion += f"Summary: {summary}"

        suggestions.append({
            'link': link,
            'suggestion': suggestion
        })

    return suggestions

@csrf_exempt
def find_shopify_stores(request):
    if request.method == 'POST':
        industry = request.POST.get('industry', '')
        location = request.POST.get('location', '')

        if not (industry and location):
            return JsonResponse({'error': 'Industry and location parameters are required'}, status=400)

        query = f'inurl:myshopify.com {industry} {location}'
        url = f"https://www.googleapis.com/customsearch/v1?key={google_api_key}&cx={search_engine_id}&q={query}"

        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad status codes
            results = response.json()
        except requests.RequestException as e:
            return JsonResponse({'error': f"Google Custom Search API error: {str(e)}"}, status=500)
        except ValueError:
            return JsonResponse({'error': 'Invalid JSON in Google Custom Search API response'}, status=500)

        final_links = []
        email_contents = []
        suggestions = []

        if not firecrawl_api_key:
            return JsonResponse({'error': 'Firecrawl API key is not set'}, status=500)

        app = FirecrawlApp(api_key=firecrawl_api_key)

        for item in results.get('items', []):
            final_links.append(item['link'])
            

            # Retry mechanism for rate limiting
            retry_count = 0
            while retry_count < 5:
                try:
                    scraped_data = app.scrape_url(item['link'])
                    if scraped_data and 'content' in scraped_data and scraped_data['content']:
                        content = scraped_data['content']
                        print("Markdown content:", content)

                        # # Split text into manageable chunks for summarization
                        # max_chunk_size = 500  # Adjust as needed
                        # chunks = [content[i:i + max_chunk_size] for i in range(0, len(content), max_chunk_size)]

                        # Summarize each chunk and concatenate results
                        brand_summary = ""
                        # for chunk in chunks:
                        #     chunk_summary = summarize_text(chunk)
                        #     brand_summary += chunk_summary + " "
                        brand_summary = summarize_text(content)
                        print("Brand Summary:", brand_summary)

                        # Use BuiltWith to get technology stacks
                        builtwith_url = f"https://api.builtwith.com/v21/api.json?KEY={builtwith_api_key}&LOOKUP={item['link']}"  #Domain API
                        # builtwith_url = f"https://api.builtwith.com/lists11/api.json?KEY={builtwith_api_key}&TECH=Shopify&LOOKUP={item['link']}"   #Lists API
                        try:
                            bw_response = requests.get(builtwith_url)
                            bw_response.raise_for_status()
                            bw_data = bw_response.json()
                            print("BuiltWith data:", bw_data)
                        except requests.RequestException as e:
                            bw_data = {'Errors': str(e)}
                        except ValueError:
                            bw_data = {'Errors': 'Invalid JSON in BuiltWith API response'}
                        

                        if bw_data.get('Errors'):
                            # Log error if there are any
                            print(f"BuiltWith API Error for {item['link']}: {bw_data['Errors']}")

                        technology_stacks = bw_data.get('Groups', [])

                        # Add backlink checking functionality
                        moz_url = f"https://lsapi.seomoz.com/v2/url_metrics?target={item['link']}&scope=page"
                        moz_headers = {
                            'Authorization': f'Basic {base64.b64encode(f"{moz_access_id}:{moz_secret_key}".encode()).decode()}'
                        }
                        try:
                            moz_response = requests.get(moz_url, headers=moz_headers)
                            moz_response.raise_for_status()
                            moz_data = moz_response.json()
                            backlink_count = moz_data.get('external_links', 0)
                            backlinks = moz_data.get('top_pages', [])  # Adjust according to the API response structure
                        except requests.RequestException as e:
                            backlink_count = 0
                            backlinks = []
                        except ValueError:
                            backlink_count = 0
                            backlinks = []


                        # Add traffic analysis functionality
                        traffic_api_url = f"https://api.similarweb.com/v1/website/{item['link']}/traffic-and-engagement/visits?api_key={similarweb_api_key}"
                        try:
                            traffic_response = requests.get(traffic_api_url)
                            traffic_response.raise_for_status()
                            traffic_data = traffic_response.json()
                            traffic_visits = traffic_data.get('visits', 0)
                            print("Traffic visits:", )
                        except requests.RequestException as e:
                            traffic_visits = 0
                        except ValueError:
                            traffic_visits = 0

                        # Generate HTML email template
                        email_subject = f"Exploring Collaboration Opportunities with {item['link']}"
                        email_body_html = render_to_string('email_template.html', {
                            'item_link': item['link'],
                            'brand_summary': brand_summary.strip(),
                            'technology_stacks': technology_stacks,
                            'backlink_count': backlink_count,
                            "backlinks": backlinks,
                            'traffic_visits': traffic_visits,
                        })
                        email_body_text = strip_tags(email_body_html)  # Strip HTML tags for text version
                        print("email_body_text:", email_body_text)

        
                        email_contents.append({
                            "link": item['link'],
                            "summary": brand_summary.strip(),
                            "technology stacks": technology_stacks,
                            "backlink_count": backlink_count,
                            "backlinks": backlinks,
                            "traffic_visits": traffic_visits,
                            "email_subject": email_subject,
                            "email_body_html": email_body_html
                        })
                    else:
                        email_contents.append({
                            "link": item['link'],
                            "summary": "No content available",
                            "email_subject": email_subject,
                            "email_body_html": "No content available"
                        })

                    break
                except requests.RequestException as e:
                    if 'rate limit exceeded' in str(e).lower():
                        retry_count += 1
                        wait_time = 2 ** retry_count
                        time.sleep(wait_time)
                    else:
                        # Log the exception for debugging
                        print(f"Error processing {item['link']}: {str(e)}")
                        email_contents.append({
                            "link": item['link'],
                            "summary": f"Error: {str(e)}",
                            "email_subject": email_subject,
                            "email_body_html": f"Error: {str(e)}"
                        })
                        break
                except Exception as e:
                    # Log any other unexpected exceptions
                    print(f"Unexpected error processing {item['link']}: {str(e)}")
                    email_contents.append({
                        "link": item['link'],
                        "summary": f"Error: {str(e)}",
                        "email_subject": email_subject,
                        "email_body_html": f"Error: {str(e)}"
                    })
                    break
        
        # Generate suggestions based on email_contents
        suggestions.extend(generate_custom_suggestions(email_contents))

        return JsonResponse({"Links": final_links, "EmailContents": email_contents, "Suggestions": suggestions})
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)
def create_call(request):
    call_result = None
    summary = None 
    analytics = None  
    lead_converted = None  
    
    if request.method == 'POST':
        form = CallForm(request.POST)
        if form.is_valid():
            # Retrieve form data
            customer_name = form.cleaned_data['name']
            phone_number = form.cleaned_data['phone_number']
            
            # Format phone number to E.164 format if needed (ensure it starts with +)
            if not phone_number.startswith('+'):
                phone_number = '+' + phone_number
            
            phone_number_id = '59269006-cf59-4a7e-b3d3-c94cf69ee940'
            system_prompt = 'TechRealm sells SEO, digital marketing, web development and more'
            system_company = 'techrealm'
            
            headers = {
                'Authorization': f'Bearer {AUTH_TOKEN}',
                'Content-Type': 'application/json',
            }

            # Prepare data payload for the API request
            data = {
                'assistant': {
                    "firstMessage": f"Hey, is this {customer_name}?",
                    "model": {
                        "provider": "openai",
                        "model": "gpt-3.5-turbo",
                        "messages": [
                            {
                                "role": "system",
                                "content": f"You are an AI bot called Jennifer. Keep the conversation short, the aim is to get the user to sign up to a calendar for a meeting. You are made to tell a customer about the solutions {system_company} offers. Our services are {system_prompt}. Keep the conversation short and address fast to get the user to sign up to a calendar for a meeting."
                            }
                        ]
                    },
                    "voice": "jennifer-playht"
                },
                'phoneNumberId': phone_number_id,
                'customer': {
                    'number': phone_number,
                    'name': customer_name,
                },
            }

            try:
                # Make the POST request to Vapi to create the phone call
                response = requests.post(f'{BASE_URL}/call/phone', headers=headers, json=data)
                response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)

                if response.status_code == 201:
                    response_data = response.json()
                    call_result = {
                        'call_id': response_data['id'],
                        'phone_number_id': response_data['phoneNumberId'],
                        'created_at': response_data['createdAt'],
                        'status': response_data['status'],
                        'cost': response_data['cost'],
                    }
                    # Fetch call summary and analytics
                    call_id = response_data['id']
                    api_key = '16ca8436-91b6-49e7-b382-60d964aaf646'  # Replace with your actual API key
                    summary = fetch_call_summary(call_id, api_key)
                    analytics = fetch_call_analytics(call_id, api_key)
                    
                    # Check if lead is converted based on analytics
                    lead_converted = 1 if check_lead(summary) else 0
                    
                else:
                    call_result = {'error': f'Failed to create call. Status code: {response.status_code}'}
            
            except requests.exceptions.RequestException as e:
                call_result = {'error': 'Failed to create call. Request error.'}
            
            except requests.exceptions.HTTPError as e:
                call_result = {'error': 'Failed to create call. HTTP error.'}
        
        else:
            call_result = {'error': 'Form validation failed.'}

    else:
        form = CallForm()

    # Render the template with form and call_result data
    return render(request, 'auth/create_call.html', {
        'form': form,
        'call_result': call_result,
        'summary': summary,
        'analytics': analytics,
        'lead_converted': lead_converted,
    })


def fetch_call_summary(call_id, api_key):
    url = f"{BASE_URL}/call/{call_id}"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    max_retries = 55
    retry_delay = 15  # seconds
    
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            call_data = response.json()
            summary = call_data.get('analysis', {}).get('summary')
            
            if summary:
                return summary
            else:
                time.sleep(retry_delay)
        else:
            return None
    
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
        return None







class DefineCallPurposeView(APIView):

    def get(self, request):
        form = CallPurposeForm()
        return render(request, 'auth/purpose.html', {'form': form})

    def post(self, request):
        form = CallPurposeForm(request.POST)
        if form.is_valid():
            goal = form.cleaned_data['goal']
            lead = form.cleaned_data['lead']
            number_to_call = form.cleaned_data['number_to_call']
            name_of_phone = form.cleaned_data['name_of_phone']
            name_of_company = form.cleaned_data['name_of_company']

            logger.debug("Validated data: %s", form.cleaned_data)

            # Generate call purpose, product suggestions, and call script using GROQ API
            api_key = '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'
            api_url = 'https://api.groq.com/openai/v1/chat/completions'

            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": (
                    f"Generate the purpose of a call for a calling agent with the following details:\n"
                    f"Goal: {goal}\n"
                    f"Lead: {lead}\n"
                    f"Number to call: {number_to_call}\n"
                    f"Name of phone: {name_of_phone}\n"
                    f"Name of company: {name_of_company}\n"
                    f"Analyze the purpose and suggest products that can be sold to this person.\n"
                    f"Also, provide a script for the call."
                )}
            ]

            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            }

            data = {
                "model": "llama3-8b-8192",
                "stream": False,
                "messages": messages
            }

            logger.debug("Sending request to GROQ API with data: %s", data)

            response = requests.post(api_url, headers=headers, json=data)

            logger.debug("GROQ API response status: %s", response.status_code)
            logger.debug("GROQ API response body: %s", response.text)

            if response.status_code == 200:
                response_data = response.json()
                if 'choices' in response_data and len(response_data['choices']) > 0:
                    choice = response_data['choices'][0].get('message', {}).get('content', '').strip()
                    return render(request, 'auth/purpose.html', {'form': form, 'call_purpose': choice})
                else:
                    return render(request, 'auth/purpose.html', {'form': form, 'error': 'Invalid response from GROQ API'})
            else:
                logger.error("GROQ API Error: %s", response.text)
                return render(request, 'auth/purpose.html', {'form': form, 'error': f'Error from GROQ API: {response.text}'})
        else:
            logger.error("Validation errors: %s", form.errors)
            return render(request, 'auth/purpose.html', {'form': form})




def check_lead(summary):
    prompt = f'You are an AI bot made to analyze summaries, your output is limited to an answer of 1 or 0. 1 stands for if the lead is converted and 0 stands for if the lead is not converted. Analyze the summary and answer in 1 or 0: {summary}'
    
    headers = {
        'Authorization': f'Bearer {LLM_API_KEY}',  # Replace with your actual API key
        'Content-Type': 'application/json',
    }
    
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(f'{LLM_BASE_URL}/v1/chat/completions', headers=headers, json=data)

    if response.status_code == 200:
        response_data = response.json()
        if 'choices' in response_data and len(response_data['choices']) > 0:
            result = response_data['choices'][0].get('message', {}).get('content', '').strip()
            return result
        else:
            return '0'  # Default to not converted if the response is not as expected
    else:
        return '0'  # Default to not converted if there's an error
