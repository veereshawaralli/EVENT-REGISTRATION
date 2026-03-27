from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import logging

logger = logging.getLogger(__name__)

from .emails import send_verification_email
from .forms import BecomeProviderForm, LoginForm, ProfileUpdateForm, SignUpForm, UserUpdateForm
from .models import UserProfile


def signup_view(request):
    """Handle user registration with email verification."""
    if request.user.is_authenticated:
        return redirect("events:event_list")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Profile created with a token by default
            UserProfile.objects.create(user=user)
            
            try:
                send_verification_email(user)
                messages.success(request, "Please check your email to verify your account.")
            except Exception as e:
                logger.error(f"Failed to send verification email to {user.email}: {e}")
                messages.warning(request, "Account created, but we couldn't send the verification email. Please try resending it.")
            
            return render(request, "accounts/verification_pending.html", {"email": user.email})
    else:
        form = SignUpForm()

    return render(request, "accounts/signup.html", {"form": form})


def verify_email(request, token):
    """Verify user's email address using the token."""
    profile = get_object_or_404(UserProfile, verification_token=token)
    if not profile.email_verified:
        profile.email_verified = True
        profile.save()
        messages.success(request, "Email verified successfully! You can now log in.")
    else:
        messages.info(request, "Email already verified.")
    return redirect("accounts:login")


def resend_verification(request):
    """Allow users to request a new verification email."""
    if request.method == "POST":
        email = request.POST.get("email")
        from django.contrib.auth.models import User
        user = User.objects.filter(email=email).first()
        if user and not user.is_superuser and not user.profile.email_verified:
            send_verification_email(user)
            messages.success(request, "Verification email resent. Please check your inbox.")
        else:
            messages.info(request, "If an account exists with that email and is unverified, an email has been sent.")
        return redirect("accounts:login")
    return render(request, "accounts/resend_verification.html")


class CustomLoginView(LoginView):
    """Custom login view with styled form and verification check."""

    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        """Check if user's email is verified before logging in."""
        user = form.get_user()
        if user.is_superuser:
            return super().form_valid(form)
            
        if not hasattr(user, 'profile') or not user.profile.email_verified:
            # We allow the login but redirect to a verification pending page 
            # OR we can just logout and show the message.
            # For simplicity, let's just show the verification pending template.
            return render(self.request, "accounts/verification_pending.html", {"email": user.email})
        return super().form_valid(form)


class CustomLogoutView(LogoutView):
    """Logout and redirect to homepage."""

    next_page = "events:event_list"


@login_required
def profile_view(request):
    """Display and update user profile."""
    # Ensure profile exists
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("accounts:profile")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile)

    context = {
        "user_form": user_form,
        "profile_form": profile_form,
        "is_provider": profile.is_provider,
    }
    return render(request, "accounts/profile.html", context)


@login_required
def become_provider(request):
    """View for regular users to apply as event organizers."""
    profile = request.user.profile
    if not request.user.is_superuser and not profile.email_verified:
        messages.warning(request, "Please verify your email address to unlock organizer features.")
        return redirect("accounts:profile")

    if profile.is_provider:
        messages.info(request, "You are already an active event organizer.")
        return redirect("events:organizer_dashboard")

    if profile.provider_status == 'pending':
        messages.info(request, "Your application is currently under review by our team.")
        return redirect("accounts:profile")

    if request.method == "POST":
        form = BecomeProviderForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.provider_status = 'pending'
            profile.save()
            messages.success(request, "Your application has been submitted and is under review.")
            return redirect("accounts:profile")
    else:
        form = BecomeProviderForm(instance=profile)

    return render(request, "accounts/become_provider.html", {"form": form})


# Note: provider_commission_checkout and provider_payment_callback removed as registration is now free.


@login_required
@require_POST
def process_provider_offline_payment(request):
    """Handle request for offline commission payment / manual activation."""
    # This view is now defunct as registration is free.
    messages.info(request, "Registration is now free. Your account will be activated upon approval.")
    return redirect("accounts:profile")
