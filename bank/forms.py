import random
import re

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django import forms

from .models import Account, Profile, Transaction

User = get_user_model()


class LoginForm(forms.Form):
    online_id = forms.CharField(label="Online ID", max_length=150)
    password = forms.CharField(label="Password", widget=forms.PasswordInput)


class RegisterForm(forms.Form):
    STATE_CHOICES = [
        ("", "Select state"),
        ("New York", "New York"),
        ("California", "California"),
        ("Texas", "Texas"),
        ("Florida", "Florida"),
        ("Illinois", "Illinois"),
        ("Pennsylvania", "Pennsylvania"),
        ("Ohio", "Ohio"),
        ("Georgia", "Georgia"),
        ("New Jersey", "New Jersey"),
        ("North Carolina", "North Carolina"),
        ("Other", "Other"),
    ]

    # Step 1 — Personal info
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    dob = forms.DateField(required=False)
    ssn = forms.CharField(max_length=11)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20)

    # Step 2 — Address
    street = forms.CharField(max_length=255)
    apt = forms.CharField(max_length=50, required=False)
    city = forms.CharField(max_length=100)
    state = forms.ChoiceField(choices=STATE_CHOICES)
    zip_code = forms.CharField(max_length=10)

    # Step 3 — Account
    account_type = forms.ChoiceField(
        choices=Profile.ACCOUNT_TYPE_CHOICES, required=False
    )
    deposit = forms.DecimalField(
        max_digits=12, decimal_places=2, required=False, min_value=0
    )

    # Step 4 — Security
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput, min_length=10)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    security_question = forms.CharField(max_length=255, required=False)
    security_answer = forms.CharField(max_length=255, required=False)

    # Step 5 — Agreements
    agree_terms = forms.BooleanField(required=True)
    agree_patriot = forms.BooleanField(required=True)

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(
                "That Online ID is already taken. Please choose another one."
            )
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )
        return email

    def clean_ssn(self):
        digits = re.sub(r"\D", "", self.cleaned_data["ssn"])
        if len(digits) != 9:
            raise forms.ValidationError("Enter a valid 9-digit SSN.")
        return digits

    def clean_password(self):
        password = self.cleaned_data["password"]
        validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Passwords do not match.")
        return cleaned_data

    def save(self):
        """Create the User and linked Profile from validated data."""
        data = self.cleaned_data
        user = User.objects.create_user(
            username=data["username"],
            email=data["email"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
        )
        profile = Profile.objects.create(
            user=user,
            date_of_birth=data.get("dob"),
            ssn_last4=data["ssn"][-4:],
            phone=data["phone"],
            street=data["street"],
            apartment=data.get("apt", ""),
            city=data["city"],
            state=data["state"],
            zip_code=data["zip_code"],
            account_type=data.get("account_type") or "checking",
            initial_deposit=data.get("deposit") or 0,
            security_question=data.get("security_question", ""),
            security_answer=data.get("security_answer", ""),
            reference_id=f"CP-{random.randint(100000, 999999)}",
        )

        # Open real, database-backed accounts to match what the customer
        # selected during registration.
        initial_deposit = data.get("deposit") or 0
        chosen = data.get("account_type") or "checking"
        if chosen in ("checking", "both"):
            Account.objects.create(
                user=user,
                account_type="checking",
                balance=initial_deposit,
            )
        if chosen in ("savings", "both"):
            Account.objects.create(
                user=user,
                account_type="savings",
                # If they opened both, the initial deposit already landed
                # in checking above; savings starts at $0 until they move
                # money over.
                balance=initial_deposit if chosen == "savings" else 0,
            )
        return user, profile


class ProfileForm(forms.Form):
    """Edits both the Django User (name/email) and linked Profile
    (phone/address) fields shown on the Settings page."""

    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20, required=False)
    street = forms.CharField(max_length=255, required=False)
    apartment = forms.CharField(max_length=50, required=False)
    city = forms.CharField(max_length=100, required=False)
    state = forms.CharField(max_length=100, required=False)
    zip_code = forms.CharField(max_length=10, required=False)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError(
                "Another account is already using this email address."
            )
        return email

    def save(self):
        data = self.cleaned_data
        user = self.user
        user.first_name = data["first_name"]
        user.last_name = data["last_name"]
        user.email = data["email"]
        user.save(update_fields=["first_name", "last_name", "email"])

        profile, _ = Profile.objects.get_or_create(user=user)
        profile.phone = data.get("phone", "")
        profile.street = data.get("street", "")
        profile.apartment = data.get("apartment", "")
        profile.city = data.get("city", "")
        profile.state = data.get("state", "")
        profile.zip_code = data.get("zip_code", "")
        profile.save(
            update_fields=[
                "phone", "street", "apartment", "city", "state",
                "zip_code", "updated_at",
            ]
        )
        return user, profile


class TransferForm(forms.Form):
    """Handles both internal (own-account) transfers and external
    (send-to-recipient) transfers."""

    from_account = forms.ModelChoiceField(queryset=Account.objects.none())
    to_choice = forms.ChoiceField(choices=[])
    recipient_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "e.g. John Davis"}),
    )
    recipient_account_number = forms.CharField(
        max_length=34,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "e.g. 000123456789"}),
    )
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(
            attrs={"placeholder": "0.00", "min": "0", "step": "0.01", "inputmode": "decimal"}
        ),
    )
    note = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "What's this for?"}),
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        accounts = Account.objects.filter(user=user, is_active=True)
        self.fields["from_account"].queryset = accounts

        choices = [
            (str(acct.pk), acct.get_account_type_display()) for acct in accounts
        ]
        choices.append(("external", "External Account (Recipient)"))
        self.fields["to_choice"].choices = choices

    def clean(self):
        cleaned_data = super().clean()
        from_account = cleaned_data.get("from_account")
        to_choice = cleaned_data.get("to_choice")
        amount = cleaned_data.get("amount")
        recipient_name = (cleaned_data.get("recipient_name") or "").strip()

        if from_account and amount and amount > from_account.balance:
            self.add_error(
                "amount", "This amount exceeds your available balance."
            )

        if to_choice == "external":
            if not recipient_name:
                self.add_error(
                    "recipient_name", "Please enter a recipient name."
                )
        elif to_choice and from_account and to_choice == str(from_account.pk):
            self.add_error("to_choice", "Choose two different accounts.")

        return cleaned_data

    def save(self, user):
        data = self.cleaned_data
        from_account = data["from_account"]
        to_choice = data["to_choice"]
        amount = data["amount"]
        note = data.get("note", "")

        if to_choice == "external":
            return Transaction.objects.create(
                user=user,
                from_account=from_account,
                to_account=None,
                transfer_type=Transaction.TRANSFER_EXTERNAL,
                recipient_name=data["recipient_name"].strip(),
                recipient_account_number=(
                    data.get("recipient_account_number") or ""
                ).strip(),
                amount=amount,
                note=note,
            )

        to_account = Account.objects.get(pk=int(to_choice), user=user)
        return Transaction.objects.create(
            user=user,
            from_account=from_account,
            to_account=to_account,
            transfer_type=Transaction.TRANSFER_INTERNAL,
            amount=amount,
            note=note,
        )
