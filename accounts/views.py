from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render

from .forms import LoginForm, ProfileUpdateForm, SignUpForm, UserUpdateForm
from .models import UserProfile


def signup_view(request):
    """Handle user registration."""
    if request.user.is_authenticated:
        return redirect("events:event_list")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create associated profile
            UserProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, f"Welcome, {user.first_name}! Your account has been created.")
            return redirect("events:event_list")
    else:
        form = SignUpForm()

    return render(request, "accounts/signup.html", {"form": form})


class CustomLoginView(LoginView):
    """Custom login view with styled form."""

    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


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
    }
    return render(request, "accounts/profile.html", context)


from django.http import HttpResponse
from django.core.mail import send_mail
from django.conf import settings

def test_email_view(request):
    """Diagnostic view to test SMTP delivery from browser."""
    if not request.user.is_superuser:
        return HttpResponse("Unauthorized", status=403)
        
    recipient = request.GET.get('email', request.user.email)
    try:
        send_mail(
            subject='EventHub SMTP Test (From Browser)',
            message='If you are reading this, your SMTP settings on Render are working perfectly!',
            from_email=None,
            recipient_list=[recipient],
            fail_silently=False,
        )
        return HttpResponse(f"Successfully sent test email to {recipient}!")
    except Exception as e:
        import traceback
        return HttpResponse(f"Failed to send email: {e}<br><br><pre>{traceback.format_exc()}</pre>")
