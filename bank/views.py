from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import TemplateView

import json

from .forms import LoginForm, ProfileForm, RegisterForm, TransferForm
from .models import Account, Profile, Transaction


class IndexView(TemplateView):
    template_name = "bank/index.html"


class RegisterView(View):
    template_name = "bank/register.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("bank:dashboard")
        return render(request, self.template_name, {"form": RegisterForm()})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user, profile = form.save()
            messages.success(
                request,
                f"Welcome to City Prime Bank, {user.first_name}! "
                f"Your reference ID is {profile.reference_id}. "
                "You can now sign on with your new Online ID.",
            )
            return redirect("bank:login")
        return render(request, self.template_name, {"form": form})


class LoginView(View):
    template_name = "bank/login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("bank:dashboard")
        return render(request, self.template_name, {"form": LoginForm()})

    def post(self, request):
        form = LoginForm(request.POST)
        error = None
        if form.is_valid():
            online_id = form.cleaned_data["online_id"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=online_id, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get("next") or request.POST.get("next")
                return redirect(next_url or "bank:dashboard")
            error = "We couldn't verify those details. Check your Online ID and password, then try again."
        else:
            error = "We couldn't verify those details. Check your Online ID and password, then try again."
        return render(
            request, self.template_name, {"form": form, "error": error}
        )


class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, "You've been signed out securely.")
        return redirect("bank:login")


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "bank/dashboard.html"
    login_url = "bank:login"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        accounts = Account.objects.filter(user=self.request.user)
        ctx["checking_account"] = accounts.filter(account_type="checking").first()
        ctx["savings_account"] = accounts.filter(account_type="savings").first()
        ctx["transactions"] = (
            Transaction.objects.filter(user=self.request.user)
            .select_related("from_account", "to_account")[:8]
        )
        return ctx


class AccountsView(LoginRequiredMixin, TemplateView):
    template_name = "bank/accounts.html"
    login_url = "bank:login"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        accounts = Account.objects.filter(user=self.request.user)
        ctx["accounts"] = accounts
        ctx["checking_account"] = accounts.filter(account_type="checking").first()
        ctx["savings_account"] = accounts.filter(account_type="savings").first()
        ctx["transactions"] = (
            Transaction.objects.filter(user=self.request.user)
            .select_related("from_account", "to_account")[:15]
        )
        return ctx


class TransferView(LoginRequiredMixin, View):
    template_name = "bank/transfer.html"
    login_url = "bank:login"

    def _context(self, request, form):
        accounts = Account.objects.filter(user=request.user)
        return {
            "form": form,
            "accounts": accounts,
            "accounts_json": json.dumps(
                {str(a.pk): float(a.balance) for a in accounts}
            ),
        }

    def get(self, request):
        form = TransferForm(user=request.user)
        return render(request, self.template_name, self._context(request, form))

    def post(self, request):
        form = TransferForm(user=request.user, data=request.POST)
        if form.is_valid():
            txn = form.save(request.user)
            ctx = self._context(request, TransferForm(user=request.user))
            ctx["completed_txn"] = txn
            return render(request, self.template_name, ctx)
        return render(request, self.template_name, self._context(request, form))


class DepositView(LoginRequiredMixin, TemplateView):
    template_name = "bank/deposit.html"
    login_url = "bank:login"


class HelpCenterView(TemplateView):
    template_name = "bank/help-center.html"


class SettingsView(LoginRequiredMixin, View):
    template_name = "bank/settings.html"
    login_url = "bank:login"

    def _profile_initial(self, user):
        profile, _ = Profile.objects.get_or_create(user=user)
        return {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": profile.phone,
            "street": profile.street,
            "apartment": profile.apartment,
            "city": profile.city,
            "state": profile.state,
            "zip_code": profile.zip_code,
        }

    def get(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        ctx = {
            "profile": profile,
            "profile_form": ProfileForm(
                request.user, initial=self._profile_initial(request.user)
            ),
            "password_form": PasswordChangeForm(request.user),
        }
        return render(request, self.template_name, ctx)

    def post(self, request):
        action = request.POST.get("action")
        profile, _ = Profile.objects.get_or_create(user=request.user)

        if action == "profile":
            profile_form = ProfileForm(request.user, data=request.POST)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(
                    request, "Your profile changes have been saved."
                )
                return redirect("bank:settings_page")
            password_form = PasswordChangeForm(request.user)

        elif action == "password":
            password_form = PasswordChangeForm(request.user, request.POST)
            profile_form = ProfileForm(
                request.user, initial=self._profile_initial(request.user)
            )
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Your password has been changed.")
                return redirect("bank:settings_page")

        else:
            return redirect("bank:settings_page")

        ctx = {
            "profile": profile,
            "profile_form": profile_form,
            "password_form": password_form,
        }
        return render(request, self.template_name, ctx)


class SettingsToggleView(LoginRequiredMixin, View):
    """Small JSON endpoint backing the instant on/off switches
    (2FA, biometric login, notification preferences) on the Settings page."""

    login_url = "bank:login"
    ALLOWED_FIELDS = {
        "two_factor_enabled",
        "biometric_enabled",
        "notify_transactions",
        "notify_low_balance",
        "notify_promotions",
    }

    def post(self, request):
        field = request.POST.get("field")
        raw_value = request.POST.get("value")
        if field not in self.ALLOWED_FIELDS or raw_value not in ("true", "false"):
            return JsonResponse({"ok": False, "error": "Invalid request."}, status=400)

        profile, _ = Profile.objects.get_or_create(user=request.user)
        value = raw_value == "true"
        setattr(profile, field, value)
        profile.save(update_fields=[field, "updated_at"])
        return JsonResponse({"ok": True, "field": field, "value": value})
