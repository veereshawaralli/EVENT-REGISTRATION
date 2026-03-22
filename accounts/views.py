import socket
import traceback
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
    # Temporarily removed restriction to allow debugging
    recipient = request.GET.get('email', 'veereshawaralli.work@gmail.com')
    try:
        sent_count = send_mail(
            subject='EventHub SMTP Test (From Browser)',
            message=f'If you are reading this, your SMTP settings on Render are working perfectly!\n\n'
                    f'Sent from: {settings.DEFAULT_FROM_EMAIL}\n'
                    f'Using Backend: {settings.EMAIL_BACKEND}\n'
                    f'Host: {settings.EMAIL_HOST}\n'
                    f'Port: {settings.EMAIL_PORT}\n'
                    f'SSL/TLS: {settings.EMAIL_USE_SSL}/{settings.EMAIL_USE_TLS}',
            from_email=None,
            recipient_list=[recipient],
            fail_silently=False,
        )
        debug_info = (
            f"<b>DEBUG INFO:</b><br>"
            f"USER: {settings.EMAIL_HOST_USER}<br>"
            f"FROM: {settings.DEFAULT_FROM_EMAIL}<br>"
            f"BACKEND: {settings.EMAIL_BACKEND}<br>"
            f"PORT: {settings.EMAIL_PORT}<br>"
            f"SSL: {settings.EMAIL_USE_SSL} | TLS: {settings.EMAIL_USE_TLS}<br>"
        )
        if sent_count > 0:
            return HttpResponse(f"Successfully sent {sent_count} test email(s) to {recipient}!<br><br>{debug_info}<br>Check your Gmail 'Sent' folder and Inbox.")
        else:
            return HttpResponse(f"Django reports 0 emails were sent (but no error occurred).<br><br>{debug_info}")
    except Exception as e:
        # Reduced Port Scan for diagnostics to avoid timeouts
        targets = [
            ("smtp.gmail.com", 587),
            ("in-v3.mailjet.com", 2525),
            ("smtp.sendgrid.net", 2525),
        ]
        scan_results = []
        for host, port in targets:
            try:
                s = socket.create_connection((host, port), timeout=2)
                s.close()
                scan_results.append(f"✅ {host}:{port}")
            except Exception as se:
                scan_results.append(f"❌ {host}:{port} ({se})")
        
        scan_info = " | ".join(scan_results)
            
        debug_info = (
            f"<b>SCAN:</b> {scan_info}<br><br>"
            f"<b>SETTINGS:</b><br>"
            f"HOST: {settings.EMAIL_HOST} | PORT: {settings.EMAIL_PORT}<br>"
            f"SSL: {settings.EMAIL_USE_SSL} | TLS: {settings.EMAIL_USE_TLS}<br>"
        )
        return HttpResponse(f"<b>Error:</b> {e}<br><br>{debug_info}<br><pre>{traceback.format_exc()}</pre>")


def test_rich_email_view(request):
    """Test the actual rich HTML registration email flow."""
    from registrations.models import Registration
    from registrations.emails import send_registration_confirmation
    import traceback
    from django.http import HttpResponse

    # Get any confirmed registration to test with
    reg = Registration.objects.filter(status="confirmed").first()
    if not reg:
        return HttpResponse("Error: No confirmed registrations found to test with. Please register for an event first.")

    try:
        # This will use fail_silently=False now
        sent = send_registration_confirmation(reg)
        
        return HttpResponse(f"""
            <h1>Rich Email Test</h1>
            <p>Attempted to send confirmation for <strong>{reg.event.title}</strong> to <strong>{reg.user.email}</strong>.</p>
            <p>Result: {'✅ Sent' if sent else '❌ Failed (Check logs)'}</p>
            <hr>
            <h3>Settings:</h3>
            <pre>
FROM: {settings.DEFAULT_FROM_EMAIL}
HOST: {settings.EMAIL_HOST}
PORT: {settings.EMAIL_PORT}
</pre>
        """)
    except Exception as e:
        return HttpResponse(f"<h1>Rich Email Error</h1><p><b>{str(e)}</b></p><pre>{traceback.format_exc()}</pre>")
