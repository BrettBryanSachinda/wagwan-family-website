from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re

class WagwanRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'w-full bg-neutral-900 border border-neutral-700 text-white px-4 py-3 focus:border-[#FF4500]'}),
    )

    class Meta:
        model = User
        fields = ('username', 'email')

    def clean_username(self):
        """Validate username: alphanumeric, underscore, hyphen only. 3-30 chars."""
        username = self.cleaned_data.get('username')
        if not username:
            raise ValidationError("Username is required.")
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters.")
        if len(username) > 30:
            raise ValidationError("Username must be under 30 characters.")
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise ValidationError("Username can only contain letters, numbers, hyphens, and underscores.")
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        """Validate email uniqueness."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already enlisted in the Wagwan Empire.")
        return email

    def clean_password2(self):
        """Ensure password is strong (at least 8 chars)."""
        password = self.cleaned_data.get('password1')
        if password and len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        return self.cleaned_data.get('password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class UserProfileForm(forms.Form):
    """Form for user profile setup with bio validation."""
    bio = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full bg-neutral-900 border border-neutral-700 text-white px-4 py-3 focus:border-[#FF4500] resize-none',
            'rows': 4,
            'placeholder': 'Tell us about yourself...'
        }),
        help_text="Maximum 500 characters. Keep it real."
    )
    profile_picture = forms.ImageField(
        required=False,
        help_text="JPG, PNG. Max 5MB. Recommended: 400x400px"
    )

    def clean_bio(self):
        """Validate bio: remove excessive whitespace, limit length."""
        bio = self.cleaned_data.get('bio', '').strip()
        if bio and len(bio) < 10:
            raise ValidationError("Bio must be at least 10 characters if provided.")
        return bio

    def clean_profile_picture(self):
        """Validate image size and format."""
        image = self.cleaned_data.get('profile_picture')
        if image:
            if image.size > 5 * 1024 * 1024:
                raise ValidationError("Image must be under 5MB.")
            if not image.content_type.startswith('image/'):
                raise ValidationError("File must be an image.")
        return image