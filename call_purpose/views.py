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
from django.contrib import messages
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
from .models import *
from .serializers import CallPurposeSerializer, CompanySerializer
from .forms import CallForm, CallPurposeForm
from firecrawl import FirecrawlApp
from groq import Groq
import time
from .utils import *

# google_key=""
# search_engine="<script async src="https://cse.google.com/cse.js?cx=2325bd1cb6f6a4a13">
# </script>
# <div class="gcse-search"></div>"


# name=Lead.objects.get('name')
# phone=Lead.objcets..get('')

google_api_key = 'AIzaSyAWzuQN69TtYbCh_nWh6nmuHxbtABnJbDw'
search_engine_id = '2325bd1cb6f6a4a13'
firecrawl_api_key = 'fc-ce7d24b36a5b463c8adbf6446a6c330e'
builtwith_api_key = os.getenv('BUILTWITH_API_KEY')
backlink_api_key = os.getenv('BACKLINK_API_KEY')
similarweb_api_key = os.getenv('SIMILARWEB_API_KEY')
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

    return render(request,'leads/index.html')


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
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        logger.debug("Attempting to authenticate user with username: %s", username)
        user = authenticate(request, username=username, password=password)  # Check password
        logger.debug("Authentication result: %s", user)
        if user is not None:
            login(request, user)
            messages.info(request, f"You are logged in as {username}")

            # Check if the user has an associated profile
            try:
                profile = user.userprofile  # Assuming you have a OneToOne relation with UserProfile
                if profile:
                    return redirect('/')  # Redirect to home if profile exists
            except UserProfile.DoesNotExist:
                pass

            return redirect('profile')  # Redirect to profile if no profile exists
        else:
            messages.error(request, "Username or Password is Incorrect")

    return render(request, 'auth/login-2.html')


@login_required
def logout_request(request):
	logout(request)
	messages.info(request, "You have successfully logged out.") 
	return redirect("/")


@login_required
def profile(request):
    if request.method == 'POST':
        # Handle form submission and save data to UserProfile model
        business_description = request.POST.get('business_description', '')
        industry = request.POST.get('industry', '')
        location = request.POST.get('location', '')
        
        # Create a new UserProfile for the current user
        user_profile = UserProfile.objects.create(
        user=request.user,
        business_description=business_description,
        industry=industry,
        location=location)
        # Optionally, you can redirect to another page after saving
        return redirect('/')  # Redirect to the same profile page after saving
        
    # Render the profile page with a form to add details
    return render(request, 'leads/profile.html')



def show_leads(request):
    leads = Lead.objects.all()
    return render(request, 'leads/show_leads.html', {'leads': leads})
    
@login_required
@csrf_exempt
def add_lead(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        contact_no = request.POST.get('contact_no')
        industry = request.POST.get('industry')
        location = request.POST.get('location')
        notes = request.POST.get('notes')

        if not (name and contact_no and industry and location):
            return JsonResponse({'error': 'Invalid input'}, status=400)

        query = f'inurl:myshopify.com {name} {industry} {location}'
        url = f"https://www.googleapis.com/customsearch/v1?key={google_api_key}&cx={search_engine_id}&q={query}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            results = response.json()
            urls = results.get('items', [])
            most_relevant_link = urls[0]['link'] if urls else None
        except requests.RequestException as e:
            return JsonResponse({'error': f"Google Custom Search API error: {str(e)}"}, status=500)
        except ValueError:
            return JsonResponse({'error': 'Invalid JSON in Google Custom Search API response'}, status=500)
        except IndexError:
            return JsonResponse({'error': 'No relevant links found'}, status=404)

        if most_relevant_link:
            app = FirecrawlApp(api_key=firecrawl_api_key)
            retry_count = 0
            while retry_count < 5:
                try:
                    scraped_data = app.scrape_url(most_relevant_link)
                    if scraped_data and 'content' in scraped_data and scraped_data['content']:
                        content = scraped_data['content']
                        result = process_website_content(most_relevant_link, content)
                        print(f"result : {result}")

                        # Parse brand summary
                        category = get_brand_category(result['brand_summary'])
                        category=category.split('**')
                        category=category[1]
                        print(f"The brand deals in: {category}")

                        parsed_summary = parse_brand_summary(result['brand_summary'])
                        logging.debug("Parsed Summary: %s", parsed_summary)
                        phone_number=parsed_summary['Phone Number']
                        print(f"Phone Number {phone_number} provided")

                        # Create a new Lead associated with the logged-in user
                        if phone_number and phone_number.lower() != 'not provided':
                            
                            lead = Lead.objects.create(
                            user=request.user,
                            link=most_relevant_link,
                            brand_summary=result['brand_summary'].strip(),
                            seo_score=result['seo_score'],
                            tech_stacks='\n'.join(result['tech_stacks']),  # Convert list to newline-separated string
                            traffic_analysis=result['traffic_analysis'],
                            name=parsed_summary['Name'] or name,
                            contact_no=contact_no,
                            industry=industry,
                            location=location,
                            notes=notes,
                            email=parsed_summary['Email'],
                            address=parsed_summary['Address'],
                            phone_number=parsed_summary['Phone Number'],
                            category=category, )
                            success_message = "Lead added successfully"
                            return JsonResponse({'status': 'Lead added', 'success_message': success_message})
                        else:
                            return JsonResponse({'status': 'error', 'error_message': 'Phone number not provided'})

                        return JsonResponse({'status': 'error', 'error_message': error_message})
                        
                except Exception as e:
                    retry_count += 1
                    if retry_count == 5:
                        return JsonResponse({'error': f"Failed to scrape the URL after multiple attempts: {str(e)}"}, status=500)
        else:
            return JsonResponse({'error': 'No relevant link found'}, status=404)

    return render(request, 'leads/add_lead.html')

@csrf_exempt
def get_or_update_lead(request, id):
    try:
        lead = Lead.objects.get(id=id)
        
        if request.method == 'PUT':
            data = json.loads(request.body)
            name = data.get('name')
            contact_no = data.get('contact_no')
            industry = data.get('industry')
            location = data.get('location')
            notes = data.get('notes')
            address = data.get('address')

            if name:
                lead.name = name
            if contact_no:
                lead.contact_no = contact_no
            if industry:
                lead.industry = industry
            if location:
                lead.location = location
            if notes:
                lead.notes = notes
            if address:
                lead.address = address

            lead.save()
            return JsonResponse({'id': lead.id, 'name': lead.name, 'industry': lead.industry, 'contact_no': lead.contact_no, 'location': lead.location, 'address': lead.address, 'status': 'Lead updated'})

        elif request.method == 'GET':
            # Handle GET request to retrieve lead details
            lead_data = {
                'id': lead.id,
                'name': lead.name,
                'contact_no': lead.contact_no,
                'industry': lead.industry,
                'location': lead.location,
                'notes': lead.notes,
                'address': lead.address
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
        Q(contact_no=query)
    )

    leads_data = [{
        'id': lead.id,
        'name': lead.name,
        'contact_no': lead.contact_no,
        'industry': lead.industry,
        'location': lead.location,
        'notes': lead.notes
    } for lead in leads]
    
    return render(request, 'leads/find_leads.html', {'leads': leads_data})


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


@csrf_exempt
@login_required
def generate_shopifystoresdetail(request):
    user = request.user
    try:
        user_profile = UserProfile.objects.get(user=user)
        industry = user_profile.industry
        location = user_profile.location
    except UserProfile.DoesNotExist:
        return JsonResponse({'error': 'User profile not found'}, status=404)

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

    if not firecrawl_api_key:
        return JsonResponse({'error': 'Firecrawl API key is not set'}, status=500)

    app = FirecrawlApp(api_key=firecrawl_api_key)

    for item in results.get('items', []):
        final_links.append(item['link'])

        retry_count = 0
        while retry_count < 5:
            try:
                scraped_data = app.scrape_url(item['link'])
                if scraped_data and 'content' in scraped_data and scraped_data['content']:
                    content = scraped_data['content']
                    brand_summary = summarize_text(content)
                    # Extract meta and slug from HTML content
                    meta, slug = extract_meta_and_slug(content)
                    # Score the website for SEO
                    seo_score = calculate_seo_score(meta, slug)
                    # Get backlinks, tech stacks, and traffic analysis
                    # backlinks = get_backlinks(item['link'])
                    tech_stacks = get_tech_stacks(item['link'])
                    traffic_analysis = get_traffic_analysis(item['link'])
                    parsed_summary = parse_brand_summary(brand_summary)

                    # phone_number=parsed_summary.get('Phone Number')
                    # if phone_number:
                    Lead.objects.create(
                        user=request.user,
                        link=item['link'],
                        brand_summary=brand_summary.strip(),
                        seo_score=seo_score,
                        tech_stacks=tech_stacks,  # Convert list to newline-separated string
                        traffic_analysis=traffic_analysis,
                        name=parsed_summary['Name'],
                        contact_no=parsed_summary['Phone Number'],
                        industry=industry,
                        location=location,
                        email=parsed_summary['Email'],
                        address=parsed_summary['Address'],
                        phone_number=parsed_summary['Phone Number']
                    )
                    


                    email_subject = f"Exploring Collaboration Opportunities with {item['link']}"
                    email_body_html = render_to_string('email_template.html', {
                        'item_link': item['link'],
                        'brand_summary': brand_summary.strip(),
                        'seo_score': seo_score,
                        # 'backlinks': backlinks,
                        'tech_stacks': tech_stacks,
                        'traffic_analysis': traffic_analysis
                    })
                    email_body_text = strip_tags(email_body_html)

                    email_contents.append({
                        "link": item['link'],
                        "summary": brand_summary.strip(),
                    })
                else:
                    email_contents.append({
                        "link": item['link'],
                        "summary": "No content available",
                    })

                break
            except requests.RequestException as e:
                if 'rate limit exceeded' in str(e).lower():
                    retry_count += 1
                    wait_time = 2 ** retry_count
                    time.sleep(wait_time)
                else:
                    print(f"Error processing {item['link']}: {str(e)}")
                    email_contents.append({
                        "link": item['link'],
                        "summary": f"Error: {str(e)}",
                    })
                    break
            except Exception as e:
                print(f"Unexpected error processing {item['link']}: {str(e)}")
                email_contents.append({
                    "link": item['link'],
                    "summary": f"Error: {str(e)}",
                })
                break
    leads = Lead.objects.all()

    # Prepare data for charts and tables
    lead_data = []
    for lead in leads:
        lead_data.append({
            'link': lead.link,
            'brand_summary': lead.brand_summary,
            'seo_score': lead.seo_score,
            'tech_stacks': lead.tech_stacks,
            'traffic_analysis': lead.traffic_analysis
        })

    return render(request, 'leads/all_leads.html', {'leads': lead_data})
 



# def create_call(request):
#     call_result = None
#     summary = None 
#     analytics = None  
#     lead_converted = None  
    
#     if request.method == 'POST':
#         form = CallForm(request.POST)
#         if form.is_valid():
#             # Retrieve form data
#             customer_name = form.cleaned_data['name']
#             phone_number = form.cleaned_data['phone_number']
            
#             # Format phone number to E.164 format if needed (ensure it starts with +)
#             if not phone_number.startswith('+'):
#                 phone_number = '+' + phone_number
            
#             phone_number_id = '59269006-cf59-4a7e-b3d3-c94cf69ee940'
#             system_prompt = 'TechRealm sells SEO, digital marketing, web development and more'
#             system_company = 'techrealm'
            
#             headers = {
#                 'Authorization': f'Bearer {AUTH_TOKEN}',
#                 'Content-Type': 'application/json',
#             }

#             # Prepare data payload for the API request
#             data = {
#                 'assistant': {
#                     "firstMessage": f"Hey, is this {customer_name}?",
#                     "model": {
#                         "provider": "openai",
#                         "model": "gpt-3.5-turbo",
#                         "messages": [
#                             {
#                                 "role": "system",
#                                 "content": f"You are an AI bot called Jennifer. Keep the conversation short, the aim is to get the user to sign up to a calendar for a meeting. You are made to tell a customer about the solutions {system_company} offers. Our services are {system_prompt}. Keep the conversation short and address fast to get the user to sign up to a calendar for a meeting."
#                             }
#                         ]
#                     },
#                     "voice": "jennifer-playht"
#                 },
#                 'phoneNumberId': phone_number_id,
#                 'customer': {
#                     'number': phone_number,
#                     'name': customer_name,
#                 },
#             }

#             try:
#                 # Make the POST request to Vapi to create the phone call
#                 response = requests.post(f'{BASE_URL}/call/phone', headers=headers, json=data)
#                 response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)

#                 if response.status_code == 201:
#                     response_data = response.json()
#                     call_result = {
#                         'call_id': response_data['id'],
#                         'phone_number_id': response_data['phoneNumberId'],
#                         'created_at': response_data['createdAt'],
#                         'status': response_data['status'],
#                         'cost': response_data['cost'],
#                     }
#                     # Fetch call summary and analytics
#                     call_id = response_data['id']
#                     api_key = '16ca8436-91b6-49e7-b382-60d964aaf646'  # Replace with your actual API key
#                     summary = fetch_call_summary(call_id, api_key)
#                     analytics = fetch_call_analytics(call_id, api_key)
                    
#                     # Check if lead is converted based on analytics
#                     lead_converted = 1 if check_lead(summary) else 0

#                     call = Call(
#                         call_id=response_data['id'],
#                         phone_number_id=response_data['phoneNumberId'],
#                         created_at=response_data['createdAt'],
#                         status=response_data['status'],
#                         cost=response_data['cost'],
#                         customer_name=customer_name,
#                         phone_number=phone_number,
#                         summary=summary,
#                         analytics=analytics,
#                         lead_converted=lead_converted
#                     )
#                     call.save()
                    
#                 else:
#                     call_result = {'error': f'Failed to create call. Status code: {response.status_code}'}
            
#             except requests.exceptions.RequestException as e:
#                 call_result = {'error': 'Failed to create call. Request error.'}
            
#             except requests.exceptions.HTTPError as e:
#                 call_result = {'error': 'Failed to create call. HTTP error.'}
        
#         else:
#             call_result = {'error': 'Form validation failed.'}

#     else:
#         form = CallForm()

#     # Render the template with form and call_result data
#     return render(request, 'auth/create_call.html', {
#         'form': form,
#         'call_result': call_result,
#         'summary': summary,
#         'analytics': analytics,
#         'lead_converted': lead_converted,
#     })


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Call
import requests

@login_required
def create_call(request):
    call_result = None
    summary = None 
    analytics = None  
    lead_converted = None

    # Get the latest call for the currently logged-in user
    latest_call = Lead.objects.filter(user=request.user).order_by('-created_at').first()

    if latest_call:
        customer_name = latest_call.name
        phone_number = latest_call.phone_number
        
        
        # Clean up phone number: remove non-digit characters and spaces, and ensure it starts with +
        phone_number = re.sub(r'\D', '', phone_number)  # Remove non-digit characters
        phone_number = re.sub(r'\s+', '', phone_number)  # Remove whitespace characters
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
        logger.debug(f'Sending payload to Vapi: {json.dumps(data, indent=2)}')

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
                print("********", call_result)
                # Fetch call summary and analytics
                call_id = response_data['id']
                api_key = '16ca8436-91b6-49e7-b382-60d964aaf646'  # Replace with your actual API key
                summary = fetch_call_summary(call_id, api_key)
                analytics = fetch_call_analytics(call_id, api_key)

                # Check if lead is converted based on analytics
                lead_converted = 1 if check_lead(summary) else 0

                # Save call details to the database
                new_call = Call(
                    
                    call_id=response_data['id'],
                    phone_number_id=response_data['phoneNumberId'],
                    created_at=response_data['createdAt'],
                    status=response_data['status'],
                    cost=response_data['cost'],
                    customer_name=customer_name,
                    phone_number=phone_number,
                    summary=summary,
                    analytics=analytics,
                    lead_converted=lead_converted
                )
                new_call.save()

            else:
                call_result = {'error': f'Failed to create call. Status code: {response.status_code}'}

        except requests.exceptions.RequestException as e:
            call_result = {'error': 'Failed to create call. Request error.'}

        except requests.exceptions.HTTPError as e:
            call_result = {'error': 'Failed to create call. HTTP error.'}

    else:
        call_result = {'error': 'No previous call found for this user.'}

    # Render the template with call_result data
    return render(request, 'auth/create_call.html', {
        'call_result': call_result,
        'summary': summary,
        'analytics': analytics,
        'lead_converted': lead_converted,
        'latest_call': latest_call,
    })


def top_ten_calls(request):
    calls = Call.objects.all().order_by('-created_at')[:10]
    print("**************",calls)
    context = {'calls': calls}
    return render(request, 'leads/top_ten_calls.html', context)

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




#Compagins Part

@csrf_exempt
@login_required
def create_calling_campaign(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        no_of_target_leads = int(request.POST.get('no_of_target_leads'))
        category = request.POST.get('category')
        call_of_action = request.POST.get('call_of_action')

        # Create the campaign
        campaign = Campaign.objects.create(
            name=name,
            no_of_target_leads=no_of_target_leads,
            category=category,
            call_of_action=call_of_action
        )

        # Fetch the required leads based on category
        leads = Lead.objects.filter(
            category=category,
            phone_number__isnull=False
        ).exclude(
            phone_number=''
        )[:no_of_target_leads]

        if not leads:
            return HttpResponse("No leads found", status=404)

        call_logs = []
        for lead in leads:
            customer_name = lead.name
            phone_number = lead.phone_number

            # Clean up phone number
            phone_number = re.sub(r'\D', '', phone_number)
            phone_number = re.sub(r'\s+', '', phone_number)
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
            logger.debug(f'Sending payload to Vapi: {json.dumps(data, indent=2)}')

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

                    # Save call details to the database
                    new_call = Call(
                        
                        call_id=response_data['id'],
                        phone_number_id=response_data['phoneNumberId'],
                        created_at=response_data['createdAt'],
                        status=response_data['status'],
                        cost=response_data['cost'],
                        customer_name=customer_name,
                        phone_number=phone_number,
                        summary=summary,
                        analytics=analytics,
                        lead_converted=lead_converted
                    )
                    call_logs.append(new_call)
                else:
                    logger.error(f'Failed to create call. Status code: {response.status_code}')

            except requests.exceptions.RequestException as e:
                logger.error('Failed to create call. Request error.', exc_info=e)

            except requests.exceptions.HTTPError as e:
                logger.error('Failed to create call. HTTP error.', exc_info=e)

        # Bulk create CallLogs for efficiency
        Call.objects.bulk_create(call_logs)
        # return redirect('campaigns_list')

        return render(request, 'leads/campaign_success.html', {'call_logs': call_logs,'campaign': campaign,'summary': summary,
             'analytics': analytics,})

    # Fetch unique categories for the dropdown
    categories = Lead.objects.values_list('category', flat=True).distinct()
    return render(request, 'leads/create_calling_compign.html', {'categories': categories})



@login_required
def campaigns_list(request):
    campaigns = Campaign.objects.all()
    return render(request, 'leads/campaigns_list.html', {'campaigns': campaigns})

