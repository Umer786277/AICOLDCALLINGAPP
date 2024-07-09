from django import forms

class CallForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        required=True,
        label='Name',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your name',
        })
    )
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        label='Phone Number',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number',
        })
    )


class CallPurposeForm(forms.Form):
    goal = forms.CharField(max_length=100, label='Goal')
    lead = forms.CharField(max_length=100, label='Lead')
    number_to_call = forms.CharField(max_length=15, label='Number to Call')
    name_of_phone = forms.CharField(max_length=100, label='Name of Phone')
    name_of_company = forms.CharField(max_length=100, label='Name of Company')