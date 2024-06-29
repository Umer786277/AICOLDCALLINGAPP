
from django.contrib.auth.models import AbstractUser
from django.db import models
import os
import json

class CustomUser(AbstractUser):
    # Define any additional fields for your user model if necessary

    # Define unique related_name for groups field to avoid clash
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_groups',  # Unique related_name
        blank=True,
        verbose_name='groups',
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
    )

    # Define unique related_name for user_permissions field to avoid clash
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions',  # Unique related_name
        blank=True,
        verbose_name='user permissions',
        help_text='Specific permissions for this user.',
    )

    def create_user_folders(self):
        # Define folder paths based on user's ID
        user_folder = os.path.join('user_data', str(self.id))
        os.makedirs(user_folder, exist_ok=True)  # Create user's main folder if it doesn't exist

        # Create additional subfolders as needed
        subfolders = ['documents', 'photos']
        for folder in subfolders:
            folder_path = os.path.join(user_folder, folder)
            os.makedirs(folder_path, exist_ok=True)

    def save_user_data_to_json(self, data):
        user_data_folder = os.path.join('user_data', str(self.id))
        os.makedirs(user_data_folder, exist_ok=True)  # Ensure user_data folder exists

        user_data_file = os.path.join(user_data_folder, 'user_data.json')
        with open(user_data_file, 'w') as file:
            json.dump(data, file)




class Company(models.Model):
    name = models.CharField(max_length=100)
    number = models.CharField(max_length=15)
    company = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name



class Call(models.Model):
    call_id = models.CharField(max_length=255)
    phone_number_id = models.CharField(max_length=255)
    created_at = models.DateTimeField()
    assistant_first_message = models.CharField(max_length=255)
    customer_number = models.CharField(max_length=20)
    status = models.CharField(max_length=50)
    cost = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.call_id

class CallSummary(models.Model):
    call = models.OneToOneField(Call, on_delete=models.CASCADE, related_name='summary')
    summary = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Summary for {self.call.call_id}'