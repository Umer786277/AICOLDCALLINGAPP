from django.shortcuts import render,redirect
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CallPurposeSerializer
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from .models import CustomUser
import logging


logger = logging.getLogger(__name__)


def index(request):

    return render(request,'call_purpose/index.html')

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

            # Generate call purpose using GROQ API
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
                    call_purpose = response_data['choices'][0].get('message', {}).get('content', '').strip()
                    return Response({'call_purpose': call_purpose}, status=status.HTTP_200_OK)
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