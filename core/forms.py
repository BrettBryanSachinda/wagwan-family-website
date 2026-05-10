from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class WagwanRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'your@email.com'}),
        help_text='Required. Used for password recovery and family updates.',
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user