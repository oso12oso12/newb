from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Account, Profile, Transaction

User = get_user_model()


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "Customer Profile"
    fk_name = "user"
    fieldsets = (
        ("Personal", {"fields": ("date_of_birth", "ssn_last4", "phone")}),
        (
            "Address",
            {"fields": ("street", "apartment", "city", "state", "zip_code")},
        ),
        ("Account", {"fields": ("account_type", "initial_deposit", "reference_id")}),
        (
            "Security Question",
            {"fields": ("security_question", "security_answer")},
        ),
    )
    readonly_fields = ("reference_id",)


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_active",
        "is_staff",
        "date_joined",
        "account_type",
    )
    list_select_related = ("profile",)

    def account_type(self, obj):
        return getattr(obj.profile, "get_account_type_display", lambda: "—")()

    account_type.short_description = "Account Type"

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "reference_id",
        "account_type",
        "city",
        "state",
        "initial_deposit",
        "created_at",
    )
    list_filter = ("account_type", "state")
    search_fields = (
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
        "reference_id",
        "city",
        "zip_code",
    )
    readonly_fields = ("reference_id", "created_at", "updated_at")


# Re-register User admin with the Profile inline attached
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "account_type",
        "account_number",
        "balance",
        "is_active",
        "updated_at",
    )
    list_filter = ("account_type", "is_active")
    search_fields = (
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
        "account_number",
    )
    readonly_fields = ("account_number", "created_at", "updated_at")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "from_account",
        "display_target",
        "transfer_type",
        "amount",
        "status",
        "created_at",
    )
    # Lets an admin change pending -> processing -> completed/failed
    # directly from the change list, no need to open each record.
    list_editable = ("status",)
    list_filter = ("status", "transfer_type", "created_at")
    search_fields = (
        "user__username",
        "user__email",
        "from_account__account_number",
        "to_account__account_number",
        "recipient_name",
        "recipient_account_number",
    )
    readonly_fields = (
        "balance_applied", "credit_applied", "refunded",
        "created_at", "updated_at",
    )
    autocomplete_fields = ("user", "from_account", "to_account")
    ordering = ("-created_at",)

admin.site.site_header = "City Prime Bank Administration"
admin.site.site_title = "City Prime Bank Admin"
admin.site.index_title = "Manage Customers & Accounts"
