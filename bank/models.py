import random

from django.conf import settings
from django.db import models


class Profile(models.Model):
    """Extra account-opening details captured during registration,
    linked one-to-one with Django's built-in User model."""

    ACCOUNT_TYPE_CHOICES = [
        ("checking", "Checking"),
        ("savings", "High Yield Savings"),
        ("both", "Checking + Savings"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    # Personal info
    date_of_birth = models.DateField(blank=True, null=True)
    ssn_last4 = models.CharField(
        "SSN (last 4 digits)", max_length=4, blank=True
    )
    phone = models.CharField(max_length=20, blank=True)

    # Address
    street = models.CharField(max_length=255, blank=True)
    apartment = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=10, blank=True)

    # Account preferences
    account_type = models.CharField(
        max_length=10, choices=ACCOUNT_TYPE_CHOICES, default="checking"
    )
    initial_deposit = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )

    # Security question (used for account-recovery demos, not password reset)
    security_question = models.CharField(max_length=255, blank=True)
    security_answer = models.CharField(max_length=255, blank=True)

    # Security & notification preferences (Settings page)
    two_factor_enabled = models.BooleanField(default=True)
    biometric_enabled = models.BooleanField(default=False)
    notify_transactions = models.BooleanField(default=True)
    notify_low_balance = models.BooleanField(default=True)
    notify_promotions = models.BooleanField(default=False)

    reference_id = models.CharField(max_length=20, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Customer Profile"
        verbose_name_plural = "Customer Profiles"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} — {self.get_account_type_display()}"

    @property
    def full_address(self):
        parts = [self.street]
        if self.apartment:
            parts.append(self.apartment)
        parts.append(f"{self.city}, {self.state} {self.zip_code}")
        return ", ".join(p for p in parts if p)


def _generate_account_number():
    return "".join(str(random.randint(0, 9)) for _ in range(12))


class Account(models.Model):
    """A single checking or savings account owned by a user.

    Real, database-backed balance — this replaces the old client-side
    (localStorage) mock balances used on the dashboard/transfer pages.
    """

    ACCOUNT_TYPE_CHOICES = [
        ("checking", "Primary Checking"),
        ("savings", "Savings Account"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="accounts",
    )
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPE_CHOICES)
    account_number = models.CharField(
        max_length=20, unique=True, default=_generate_account_number
    )
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "account_type")
        ordering = ["account_type"]

    def __str__(self):
        return f"{self.get_account_type_display()} •••• {self.last4} ({self.user})"

    @property
    def last4(self):
        return self.account_number[-4:]


class Transaction(models.Model):
    """A transfer/payment record.

    Transfers are created in `pending` status. Balances are only moved once
    an admin marks the transaction `completed` — this is the manual
    review workflow requested until an automated processing pipeline
    (the "next feature") is built.
    """

    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_COMPLETED, "Successful"),
        (STATUS_FAILED, "Failed"),
    ]

    TRANSFER_INTERNAL = "internal"
    TRANSFER_EXTERNAL = "external"
    TRANSFER_TYPE_CHOICES = [
        (TRANSFER_INTERNAL, "Internal Transfer"),
        (TRANSFER_EXTERNAL, "External Transfer"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transactions",
        help_text="The account holder who initiated this transfer.",
    )
    from_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name="outgoing_transactions",
    )
    to_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name="incoming_transactions",
        null=True,
        blank=True,
        help_text="Only set for internal transfers between the user's own accounts.",
    )
    transfer_type = models.CharField(max_length=10, choices=TRANSFER_TYPE_CHOICES)
    recipient_name = models.CharField(max_length=150, blank=True)
    recipient_account_number = models.CharField(max_length=34, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    note = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    balance_applied = models.BooleanField(
        default=False,
        help_text="Internal flag — set once the transfer amount has been "
        "held (debited from the source account). This happens immediately "
        "when the transfer is submitted, not when it's marked completed.",
    )
    credit_applied = models.BooleanField(
        default=False,
        help_text="Internal flag — set once the destination account has "
        "been credited (internal transfers only), which happens when the "
        "transaction is marked completed.",
    )
    refunded = models.BooleanField(
        default=False,
        help_text="Internal flag — set if a held transfer was later marked "
        "failed and the funds were returned to the source account.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        target = self.recipient_name if self.transfer_type == self.TRANSFER_EXTERNAL else self.to_account
        return f"{self.from_account} → {target}: ${self.amount} ({self.status})"

    @property
    def display_target(self):
        if self.transfer_type == self.TRANSFER_EXTERNAL:
            return self.recipient_name
        return self.to_account.get_account_type_display() if self.to_account else "—"

    def _apply_hold(self):
        """Debit the source account the moment the transfer is submitted,
        so the money is set aside while the transfer is pending review —
        the same way a pending charge holds funds at a real bank."""
        if self.balance_applied:
            return
        from_acct = Account.objects.select_for_update().get(pk=self.from_account_id)
        from_acct.balance -= self.amount
        from_acct.save(update_fields=["balance", "updated_at"])
        self.balance_applied = True

    def _apply_completion_credit(self):
        """Once an internal transfer is marked completed, credit the
        destination account. The source side was already debited as a
        hold when the transfer was created."""
        if self.credit_applied:
            return
        if self.transfer_type == self.TRANSFER_INTERNAL and self.to_account_id:
            to_acct = Account.objects.select_for_update().get(pk=self.to_account_id)
            to_acct.balance += self.amount
            to_acct.save(update_fields=["balance", "updated_at"])
        self.credit_applied = True

    def _refund_hold(self):
        """If a transfer fails after funds were held, return them to the
        source account. No-op if the destination was already credited
        (i.e. it was already completed)."""
        if self.refunded or not self.balance_applied or self.credit_applied:
            return
        from_acct = Account.objects.select_for_update().get(pk=self.from_account_id)
        from_acct.balance += self.amount
        from_acct.save(update_fields=["balance", "updated_at"])
        self.refunded = True

    def save(self, *args, **kwargs):
        from django.db import transaction as db_transaction

        is_new = self.pk is None
        previous_status = None
        if not is_new:
            previous_status = (
                Transaction.objects.filter(pk=self.pk)
                .values_list("status", flat=True)
                .first()
            )

        becoming_completed = (
            not is_new
            and self.status == self.STATUS_COMPLETED
            and previous_status != self.STATUS_COMPLETED
        )
        becoming_failed = (
            not is_new
            and self.status == self.STATUS_FAILED
            and previous_status != self.STATUS_FAILED
        )

        with db_transaction.atomic():
            if is_new:
                self._apply_hold()
            if becoming_completed:
                self._apply_completion_credit()
            if becoming_failed:
                self._refund_hold()
            super().save(*args, **kwargs)
