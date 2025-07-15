from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': '', 'class': 'form-input'})
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': '', 'class': 'form-input'})
    )
    password1 = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={'placeholder': '', 'class': 'form-input'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        strip=False,
        widget=forms.PasswordInput(attrs={'placeholder': '', 'class': 'form-input'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    #endclass

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        #endif
        return email
    #enddef
#endclass