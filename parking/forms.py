from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from .models import StudentProfile, Vehicle, ParkingLot, Reservation
import re


class _AuthFieldMixin:
    """
    Mixin that enriches auth form widgets for floating labels, accessibility, and RTL-readiness.
    """

    AUTOCOMPLETE_HINTS = {
        "username": "username",
        "email": "email",
        "phone": "tel",
        "password": "current-password",
        "password1": "new-password",
        "password2": "new-password",
        "first_name": "given-name",
        "last_name": "family-name",
    }

    INPUTMODE_HINTS = {
        "username": "email",
        "email": "email",
        "phone": "tel",
    }

    def _auto_id_for(self, name: str) -> str | None:
        auto_id = getattr(self, "auto_id", None)
        if not auto_id:
            return None
        if "%s" in str(auto_id):
            return str(auto_id) % self.add_prefix(name)
        return str(auto_id)

    def _init_accessible_widgets(self) -> None:
        for name, field in self.fields.items():
            widget = field.widget
            attrs = widget.attrs.copy()

            attrs.pop("placeholder", None)
            attrs.setdefault("dir", "auto")
            attrs.setdefault("aria-invalid", "false")

            autocomplete = self.AUTOCOMPLETE_HINTS.get(name)
            if autocomplete:
                attrs["autocomplete"] = autocomplete

            inputmode = self.INPUTMODE_HINTS.get(name)
            if inputmode:
                attrs["inputmode"] = inputmode

            if name in {"username", "email"}:
                attrs.setdefault("autocapitalize", "none")
                attrs.setdefault("spellcheck", "false")

            if name == "phone":
                attrs.setdefault("pattern", r"[\d\s\+\-\(\)]{6,}")

            attrs.setdefault("data-validate", name)
            attrs.setdefault("aria-required", "true" if field.required else "false")

            if field.help_text:
                described = self._auto_id_for(name)
                if described:
                    attrs.setdefault("aria-describedby", f"{described}_help")

            widget.attrs = attrs


class StudentSignupForm(_AuthFieldMixin, UserCreationForm):
    email = forms.EmailField(
        required=True,
        label=_("Email address"),
        widget=forms.EmailInput(),
        help_text=_("We’ll send receipts and verification updates here."),
    )
    phone = forms.CharField(
        required=False,
        label=_("Phone number"),
        widget=forms.TextInput(),
        help_text=_("Optional. Helps with SMS updates and recovery."),
    )
    first_name = forms.CharField(
        required=True,
        label=_("First name"),
        widget=forms.TextInput(),
    )
    last_name = forms.CharField(
        required=True,
        label=_("Last name"),
        widget=forms.TextInput(),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["username"].label = _("Username")
        self.fields["username"].help_text = _(
            "Lowercase letters, numbers, and @/./+/-/_"
        )
        self.fields["password1"].help_text = _(
            "Use at least 8 characters with a mix of upper/lowercase, numbers, and symbols."
        )
        self.fields["password2"].help_text = _("Repeat your password for confirmation.")

        self._init_accessible_widgets()

        self.fields["password1"].widget.attrs.setdefault("data-validate", "password")
        self.fields["password2"].widget.attrs.setdefault(
            "data-validate", "password-confirm"
        )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_("This email is already registered."))
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "")
        if phone:
            phone_digits = re.sub(r"\D", "", phone)
            if not 10 <= len(phone_digits) <= 15:
                raise forms.ValidationError(_("Please enter a valid phone number."))
            return phone_digits
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]

        if commit:
            user.save()
            StudentProfile.objects.create(
                user=user,
                phone_number=self.cleaned_data.get("phone"),
            )
        return user


class StudentLoginForm(_AuthFieldMixin, forms.Form):
    username = forms.CharField(
        label=_("Email or phone"),
        widget=forms.TextInput(),
        help_text=_("Use the email or phone number linked to your account."),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(),
        label=_("Password"),
        help_text=_("Your password is case-sensitive."),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._init_accessible_widgets()
        self.fields["password"].widget.attrs.setdefault("data-validate", "password")


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
                'placeholder': 'e.g., B 123456',
                'pattern': '[A-Za-z]\s\d{2,8}',
                'title': 'Lebanese format: one letter followed by 2-8 digits'
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
            formatted_plate = re.sub(r'\s+', '', license_plate.upper().strip())

            match = re.fullmatch(r'([A-Z])(\d{2,8})', formatted_plate or '')
            if not match:
                raise forms.ValidationError(
                    "Invalid Lebanese license plate format. Use format like: B 123456"
                )

            return f"{match.group(1)} {match.group(2)}"
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
                format='%Y-%m-%dT%H:%M'  
            ),
            'end_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control', 'step': 300},
                format='%Y-%m-%dT%H:%M' 
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure the format is accepted properly
        for field in ['start_time', 'end_time']:
            self.fields[field].input_formats = ['%Y-%m-%dT%H:%M']