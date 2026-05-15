from django import forms
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from .models import User, service, elevators


class CustomUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)

        for fieldname in ['username', 'password2']:
            self.fields[fieldname].help_text = None

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name',
                  'phone_number', 'address', 'region', 'email', 'password1', 'password2', 'profile_pic', ]

        exclude = ('password1.help_text',)


class ServiceForm(ModelForm):
    class Meta:
        model = service
        fields = '__all__'
        exclude = ('comment',)

        widgets = {
            'elevator_id': forms.Select(attrs={'class': 'dropdown_menu col-md-12'}),
            'stuff_id': forms.Select(attrs={'class': 'dropdown_menu'}),


        }


class CommentServiceForm(ModelForm):
    class Meta:
        model = service
        fields = 'comment',

        widgets = {
            'comment': forms.Textarea(attrs={
                "class": "dropdown_menu",
                'style': 'width: 450px; height:150px; resize:none; text-align: left; ',
                "rows": "3",

            }),

        }


class ElevatorForm(ModelForm):
    class Meta:
        model = elevators
        fields = '__all__'

        widgets = {
            'control_panel': forms.TextInput(attrs={'class': 'dropdown_menu'}),
            'client_id': forms.Select(attrs={'class': 'dropdown_menu'}),
            'elevator_type': forms.Select(attrs={'class': 'dropdown_menu'})
        }


class paswdChange(ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name',
                  'phone_number', 'address', 'region', 'email', 'password']


class UpdateUser(ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name',
                  'phone_number', 'address', 'region', 'email']
