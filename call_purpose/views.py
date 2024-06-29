from django.shortcuts import render,redirect
import requests
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status,generics
from .serializers import CallPurposeSerializer, CompanySerializer
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from .models import CustomUser, Company, Call, CallSummary
from django.http import JsonResponse
import requests
import logging
from django.views.decorators.csrf import csrf_exempt
from .utils import create_vapi_call
import json



logger = logging.getLogger(__name__)


def index(request):

    return render(request,'call_purpose/index.html')


@api_view(['POST'])
def create_company(request):
    if request.method == 'POST':
        serializer = CompanySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



def retrieve_person(request, pk):
    try:
        person = Company.objects.get(pk=pk)
        data = {
            'name': person.name,
            'number': person.number,
            'company': person.company,
            'description': person.description,
        }
        return JsonResponse(data)
    except Company.DoesNotExist:
        return JsonResponse({'error': 'Person not found'}, status=404)
    



# def call_response(request):
#     api_url = 'http://127.0.0.1:8000/api/retrieve-person/1/'  # Replace with the actual URL of the API service

#     try:
#         response = requests.get(api_url)
#         response_data = response.json()
#         return JsonResponse(response_data)
#     except requests.exceptions.RequestException as e:
#         return JsonResponse({'error': str(e)}, status=500)

# class CallResponseView(APIView):

#     def get(self, request, call_id):
#         api_url = f"https://api.vapi.ai/call/{call_id}"
#         token = "c25925e6-8ee8-4d00-9ef1-52bb115ef542"  
#         headers = {"Authorization": f"Bearer {token}"}

#         try:
#             response = requests.get(api_url, headers=headers)
#             response.raise_for_status()
#             data = response.json()
#             return Response(data, status=status.HTTP_200_OK)
#         except requests.exceptions.HTTPError as err:
#             return Response({'error': str(err)}, status=response.status_code)
#         except requests.exceptions.RequestException as e:
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CallResponseView(generics.RetrieveAPIView):
    queryset = Company.objects.all()  
    serializer_class = CompanySerializer

    def get(self, request, pk):
        try:
            company = self.queryset.get(pk=pk)
            serializer = self.serializer_class(company)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Company.DoesNotExist:
            return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)

class DefineCallPurposeView(APIView):

    def post(self, request):
        logger.debug("Received request data: %s", request.data)
        
        serializer = CallPurposeSerializer(data=request.data)
        if serializer.is_valid():
            goal = serializer.validated_data['goal']
            lead = serializer.validated_data['lead']
            number_to_call = serializer.validated_data['number_to_call']
            name_of_phone = serializer.validated_data['name_of_phone']
            name_of_company = serializer.validated_data['name_of_company']

            logger.debug("Validated data: %s", serializer.validated_data)

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
                    return Response({'response': choice}, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'Invalid response from GROQ API'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                logger.error("GROQ API Error: %s", response.text)
                return Response({'error': f'Error from GROQ API: {response.text}'}, status=response.status_code)
        else:
            logger.error("Validation errors: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)







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

    return render(request, 'call_purpose/signup.html')





def signin(request):
    if request.user.is_authenticated:
        messages.warning(request, "You are already logged in")
        return redirect('/')
    else:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            logger.debug("Attempting to authenticate user with username: %s", username)
            user = authenticate(request, username=username, password=password)  # Check password
            logger.debug("Authentication result: %s", user)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are logged in as {username}")
                return redirect('index')
            else:
                messages.error(request, "Username or Password is Incorrect")

    return render(request, 'call_purpose/signin.html')





@login_required
def logout_request(request):
	logout(request)
	messages.info(request, "You have successfully logged out.") 
	return redirect("/")





@csrf_exempt
def create_call(request):
    if request.method == 'POST':
        # Your Vapi API Authorization token
        auth_token = '16ca8436-91b6-49e7-b382-60d964aaf646'
        # The Phone Number ID, and the Customer details for the call
        phone_number_id = '59269006-cf59-4a7e-b3d3-c94cf69ee940'
        customer_number = "+18722589898"

        # Create the header with Authorization token
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json',
        }

        # Create the data payload for the API request
        data = {
            'assistant': {
                "firstMessage": "Hey, what's up?",
                "model": {
                    "provider": "openai",
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an assistant."
                        }
                    ]
                },
                "voice": "jennifer-playht"
            },
            'phoneNumberId': phone_number_id,
            'customer': {
                'number': customer_number,
            },
        }

        # Make the POST request to Vapi to create the phone call
        response = requests.post(
            'https://api.vapi.ai/call/phone', headers=headers, json=data)

        # Check if the request was successful and save the necessary call data
        if response.status_code == 201:
            response_data = response.json()
            call = Call(
                call_id=response_data['id'],
                phone_number_id=response_data['phoneNumberId'],
                created_at=response_data['createdAt'],
                assistant_first_message=response_data['assistant']['firstMessage'],
                customer_number=response_data['customer']['number'],
                status=response_data['status'],
                cost=response_data['cost'],
            )
            call.save()

            return JsonResponse({'message': 'Call created successfully', 'data': response.json()}, status=201)
        else:
            return JsonResponse({'message': 'Failed to create call', 'error': response.text}, status=response.status_code)

    return JsonResponse({'message': 'Invalid request method'}, status=405)


# Your Vapi API Authorization token
AUTH_TOKEN = '16ca8436-91b6-49e7-b382-60d964aaf646'

# Base URL for Vapi API
BASE_URL = 'https://api.vapi.ai'

# Headers for API requests
HEADERS = {
    'Authorization': f'Bearer {AUTH_TOKEN}',
    'Content-Type': 'application/json',
}

@csrf_exempt
def get_call_summary(request, call_id):
    try:
        call = Call.objects.get(call_id=call_id)
    except Call.DoesNotExist:
        return JsonResponse({'message': 'Call not found'}, status=404)

    response = requests.get(f'{BASE_URL}/call/{call_id}', headers=HEADERS)

    if response.status_code == 200:
        response_data = response.json()
        summary = response_data.get('analysis', {}).get('summary', '')

        # Save the summary in the database
        call_summary, created = CallSummary.objects.get_or_create(call=call)
        call_summary.summary = summary
        call_summary.save()

        return JsonResponse({'message': 'Call summary retrieved successfully', 'summary': summary}, status=200)
    else:
        return JsonResponse({'message': 'Failed to retrieve call summary', 'error': response.text}, status=response.status_code)





# Your LLM API details (e.g., GROQ Llama 80B)
LLM_API_KEY = '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'
LLM_BASE_URL = 'https://api.groq.com/openai/v1/chat/completions'  # Adjust as needed
LLM_HEADERS = {
    'Authorization': f'Bearer {LLM_API_KEY}',
    'Content-Type': 'application/json',}


@csrf_exempt
def send_to_llm(request):
    if request.method != 'POST':
        return JsonResponse({'message': 'Method not allowed'}, status=405)

    call_id = request.POST.get('call_id')
    if not call_id:
        return JsonResponse({'message': 'Call ID is required'}, status=400)

    # Step 1: Get the summary using the existing function
    summary_response = get_call_summary(request, call_id)
    
    if summary_response.status_code != 200:
        return summary_response  # Return the error response if summary retrieval failed

    summary_data = json.loads(summary_response.content)
    summary = summary_data.get('summary', '')

    # Step 2: Send the summary to the LLM for analysis
    llm_data = {
        "model": "llama3-8b-8192",  # Adjust based on the specific GROQ model you're using
        "messages": [
            # {"role": "system", "content": "You are an AI assistant that analyzes call summaries."},
            {"role": "user", "content": f"Analyze this call summary and provide insights: {summary}"}
        ],
        "temperature": 0.7
    }

    llm_response = requests.post(LLM_BASE_URL, headers=LLM_HEADERS, json=llm_data)

    if llm_response.status_code != 200:
        return JsonResponse({'message': 'Failed to analyze summary with LLM', 'error': llm_response.text}, status=llm_response.status_code)

    llm_analysis = llm_response.json()['choices'][0]['message']['content']

    # Step 3: Save the analysis results
    try:
        call = Call.objects.get(call_id=call_id)
        call_summary, created = CallSummary.objects.get_or_create(call=call)
        call_summary.llm_analysis = llm_analysis
        call_summary.save()
    except Call.DoesNotExist:
        return JsonResponse({'message': 'Call not found'}, status=404)

    return JsonResponse({
        'message': 'Call summary analyzed successfully',
        # 'summary': summary,
        'llm_analysis': llm_analysis
    }, status=200)