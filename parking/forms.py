from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from .models import StudentProfile, Vehicle, ParkingLot, Reservation
import re

class StudentSignupForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email'
    }))
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your phone number'
    }))
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'First Name'
    }))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Last Name'
    }))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove all non-digit characters
            phone_digits = re.sub(r'\D', '', phone)
            if len(phone_digits) < 10 or len(phone_digits) > 15:
                raise forms.ValidationError("Please enter a valid phone number.")
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            # Create student profile
            StudentProfile.objects.create(
                user=user,
                phone_number=self.cleaned_data.get('phone')
            )
        return user

class StudentLoginForm(forms.Form):
    email_or_phone = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email or Phone Number'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['make', 'model', 'year', 'license_plate', 'color', 'is_primary']
        widgets = {
            'make': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Toyota, Honda, Ford'
            }),
            'model': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Camry, Civic, F-150'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2020',
                'min': '1990',
                'max': '2025'
            }),
            'license_plate': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., ABC 123',
                'pattern': '.*',
                'title': 'Lebanese format: ABC 123'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Red, Blue, Black'
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def clean_license_plate(self):
        license_plate = self.cleaned_data.get('license_plate')
        if license_plate:
            # Format Lebanese license plate (keep space, convert to uppercase)
            formatted_plate = re.sub(r'\s+', ' ', license_plate.upper().strip())
            
            # Validate Lebanese format
            lebanese_patterns = [
                r'^\d{2,3}\s[A-Z]{2,3}$',  # 123 ABC, 12 AB
                r'^[A-Z]{2,3}\s\d{2,3}$',  # ABC 123, AB 12
            ]
            
            if not any(re.match(pattern, formatted_plate) for pattern in lebanese_patterns):
                raise forms.ValidationError(
                    "Invalid Lebanese license plate format. "
                    "Use format like: 123 ABC or ABC 123"
                )
            
            return formatted_plate
        return license_plate

    def clean_year(self):
        year = self.cleaned_data.get('year')
        from datetime import datetime
        current_year = datetime.now().year
        if year and (year < 1990 or year > current_year + 1):
            raise forms.ValidationError(f"Please enter a valid year between 1990 and {current_year + 1}")
        return year

class ParkingLotSearchForm(forms.Form):
    query = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Search by name or address...'
    }))
    latitude = forms.DecimalField(required=False, widget=forms.HiddenInput())
    longitude = forms.DecimalField(required=False, widget=forms.HiddenInput())
    
    SORT_CHOICES = [
        ('distance', 'Nearest First'),
        ('price_low', 'Price: Low to High'),
        ('price_high', 'Price: High to Low'),
        ('availability', 'Most Available'),
    ]
    
    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='distance',
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['vehicle', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control', 'step': 300},
                format='%Y-%m-%dT%I:%M'  # 12-hour format
            ),
            'end_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control', 'step': 300},
                format='%Y-%m-%dT%I:%M'  # 12-hour format
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure the format is accepted properly
        for field in ['start_time', 'end_time']:
            self.fields[field].input_formats = ['%Y-%m-%dT%I:%M']