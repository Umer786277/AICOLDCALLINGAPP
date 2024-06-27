
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser

@receiver(post_save, sender=CustomUser)
def handle_user_registration(sender, instance, created, **kwargs):
    if created:
        instance.create_user_folders()
        # Optionally save initial user data
        initial_data = {'username': instance.username, 'email': instance.email}
        instance.save_user_data_to_json(initial_data)
