# Generated by Django 3.2.16 on 2024-06-28 09:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('call_purpose', '0003_calldetail'),
    ]

    operations = [
        migrations.CreateModel(
            name='VapiCall',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('call_id', models.CharField(max_length=255, unique=True)),
                ('status', models.CharField(max_length=50)),
                ('customer_number', models.CharField(max_length=20)),
                ('customer_name', models.CharField(max_length=255)),
                ('twilio_phone_number', models.CharField(max_length=20)),
                ('assistant_name', models.CharField(max_length=255)),
                ('first_message', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                ('duration', models.IntegerField(blank=True, null=True)),
                ('cost', models.DecimalField(blank=True, decimal_places=4, max_digits=10, null=True)),
                ('transcript', models.TextField(blank=True)),
                ('recording_url', models.URLField(blank=True)),
                ('full_response', models.JSONField()),
            ],
        ),
    ]