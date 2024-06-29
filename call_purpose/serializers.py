from rest_framework import serializers
from .models import Company


class CallPurposeSerializer(serializers.Serializer):
    goal = serializers.CharField(max_length=255)
    lead = serializers.CharField(max_length=255)
    number_to_call = serializers.CharField(max_length=20)
    name_of_phone = serializers.CharField(max_length=255)
    name_of_company = serializers.CharField(max_length=255)




class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['name', 'number', 'company', 'description']
