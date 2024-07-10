# Generated by Django 3.2.16 on 2024-06-29 10:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('call_purpose', '0004_vapicall'),
    ]

    operations = [
        migrations.CreateModel(
            name='Call',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('call_id', models.CharField(max_length=255)),
                ('phone_number_id', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField()),
                ('assistant_first_message', models.CharField(max_length=255)),
                ('customer_number', models.CharField(max_length=20)),
                ('status', models.CharField(max_length=50)),
                ('cost', models.DecimalField(decimal_places=2, max_digits=10)),
            ],
        ),
        migrations.DeleteModel(
            name='CallDetail',
        ),
        migrations.DeleteModel(
            name='VapiCall',
        ),
    ]