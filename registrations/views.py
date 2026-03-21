from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from events.models import Event

from .models import Registration, Waitlist


def _send_registration_email(user, event, action="registered"):
    subject_map = {
        "registered": f"✅ Registered: {event.title}",
        "cancelled": f"❌ Cancelled: {event.title}",
        "waitlisted": f"⏳ Waitlisted: {event.title}",
        "promoted": f"🎉 Spot Available: {event.title}",
    }
    body_map = {
        "registered": (
            f"Hi {user.first_name or user.username},\n\n"
            f"You've successfully registered for {event.title}.\n"
            f"📅 Date: {event.date.strftime('%B %d, %Y')} at {event.time.strftime('%I:%M %p')}\n"
            f"📍 Location: {event.location}\n\n"
            f"See you there!\n— EventHub Team"
        ),
        "cancelled": (
            f"Hi {user.first_name or user.username},\n\n"
            f"Your registration for {event.title} has been cancelled.\n"
            f"If you change your mind, you can re-register anytime.\n\n"
            f"— EventHub Team"
        ),
        "waitlisted": (
            f"Hi {user.first_name or user.username},\n\n"
            f"{event.title} is currently full. You've been added to the waitlist.\n"
            f"We'll notify you if a spot opens up!\n\n"
            f"— EventHub Team"
        ),
        "promoted": (
            f"Hi {user.first_name or user.username},\n\n"
            f"Great news! A spot opened up for {event.title}.\n"
            f"Please log in to confirm your registration.\n\n"
            f"— EventHub Team"
        ),
    }
    try:
        send_mail(
            subject=subject_map.get(action, "EventHub Notification"),
            message=body_map.get(action, ""),
            from_email=None,  # Uses DEFAULT_FROM_EMAIL from settings
            recipient_list=[user.email],
            fail_silently=True,
        )
    except Exception:
        pass


@login_required
def register_for_event(request, event_id):
    """Register the current user for an event."""
    event = get_object_or_404(Event, pk=event_id)

    if request.method != "POST":
        return redirect("events:event_detail", pk=event_id)

    # Check if event has already passed
    if not event.is_upcoming:
        messages.error(request, "This event has already taken place.")
        return redirect("events:event_detail", pk=event_id)

    # Check for existing confirmed registration
    existing = Registration.objects.filter(
        user=request.user, event=event, status="confirmed"
    ).exists()
    if existing:
        messages.warning(request, "You are already registered for this event.")
        return redirect("events:event_detail", pk=event_id)

    # If event is full → send to waitlist
    if event.is_full:
        try:
            Waitlist.objects.create(user=request.user, event=event)
            _send_registration_email(request.user, event, action="waitlisted")
            messages.warning(
                request,
                f"The event is full! You've been added to the waitlist (position #{event.waitlist_count}).",
            )
        except IntegrityError:
            messages.warning(request, "You are already on the waitlist for this event.")
        return redirect("events:event_detail", pk=event_id)

    # Check for a previously cancelled registration and reactivate it
    cancelled_reg = Registration.objects.filter(
        user=request.user, event=event, status="cancelled"
    ).first()
    if cancelled_reg:
        cancelled_reg.status = "confirmed"
        cancelled_reg.save()
        _send_registration_email(request.user, event, action="registered")
        messages.success(request, f"You have been re-registered for {event.title}!")
        return redirect("events:event_detail", pk=event_id)

    # Create new registration
    try:
        Registration.objects.create(user=request.user, event=event, status="confirmed")
        _send_registration_email(request.user, event, action="registered")
        messages.success(request, f"Successfully registered for {event.title}!")
    except IntegrityError:
        messages.error(request, "Registration failed. Please try again.")

    return redirect("events:event_detail", pk=event_id)


@login_required
def cancel_registration(request, registration_id):
    """Cancel an existing registration and promote next waitlist user."""
    registration = get_object_or_404(
        Registration, pk=registration_id, user=request.user, status="confirmed"
    )

    if request.method == "POST":
        registration.status = "cancelled"
        registration.save()
        _send_registration_email(request.user, registration.event, action="cancelled")
        messages.success(
            request,
            f"Your registration for {registration.event.title} has been cancelled.",
        )
        # Promote first waitlist user
        next_waiter = Waitlist.objects.filter(event=registration.event).first()
        if next_waiter:
            _send_registration_email(next_waiter.user, registration.event, action="promoted")
            next_waiter.delete()

    return redirect("registrations:dashboard")


@login_required
def join_waitlist(request, event_id):
    """Directly join the waitlist for a full event."""
    event = get_object_or_404(Event, pk=event_id)
    if request.method == "POST":
        try:
            Waitlist.objects.create(user=request.user, event=event)
            _send_registration_email(request.user, event, action="waitlisted")
            messages.success(request, f"You've been added to the waitlist for {event.title}.")
        except IntegrityError:
            messages.warning(request, "You are already on the waitlist.")
    return redirect("events:event_detail", pk=event_id)


@login_required
def leave_waitlist(request, event_id):
    """Leave the waitlist for an event."""
    event = get_object_or_404(Event, pk=event_id)
    entry = Waitlist.objects.filter(user=request.user, event=event).first()
    if request.method == "POST" and entry:
        entry.delete()
        messages.success(request, f"You've been removed from the waitlist for {event.title}.")
    return redirect("events:event_detail", pk=event_id)


@login_required
def download_ics(request, registration_id):
    """Download an .ics calendar file for a confirmed registration."""
    registration = get_object_or_404(
        Registration, pk=registration_id, user=request.user, status="confirmed"
    )
    event = registration.event

    # Build RFC5545-compliant ICS content
    from datetime import datetime
    import uuid

    dt_start = datetime.combine(event.date, event.time)
    dt_end = datetime(dt_start.year, dt_start.month, dt_start.day,
                      dt_start.hour + 2, dt_start.minute)  # default 2h duration
    now = datetime.utcnow()
    uid = str(uuid.uuid4())

    ics_content = (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//EventHub//EN\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:{uid}\r\n"
        f"DTSTAMP:{now.strftime('%Y%m%dT%H%M%SZ')}\r\n"
        f"DTSTART:{dt_start.strftime('%Y%m%dT%H%M%S')}\r\n"
        f"DTEND:{dt_end.strftime('%Y%m%dT%H%M%S')}\r\n"
        f"SUMMARY:{event.title}\r\n"
        f"DESCRIPTION:{event.description[:500].replace(chr(10), '\\n')}\r\n"
        f"LOCATION:{event.location}\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )

    response = HttpResponse(ics_content, content_type="text/calendar")
    safe_title = event.title.replace(" ", "_")[:30]
    response["Content-Disposition"] = f'attachment; filename="{safe_title}.ics"'
    return response


@login_required
def mark_attended(request, registration_id):
    """Toggle attendance for a registration (organizer or staff only)."""
    registration = get_object_or_404(Registration, pk=registration_id)
    event = registration.event
    if not (request.user.is_staff or event.organizer == request.user):
        messages.error(request, "You don't have permission to mark attendance.")
        return redirect("events:event_detail", pk=event.pk)

    if request.method == "POST":
        registration.attended = not registration.attended
        registration.save(update_fields=["attended"])
        status_text = "attended" if registration.attended else "not attended"
        messages.success(request, f"Marked {registration.user.username} as {status_text}.")
        
        # Check if they came from the verification page
        if 'HTTP_REFERER' in request.META and 'verify' in request.META['HTTP_REFERER']:
            return redirect("registrations:verify_ticket", registration_id=registration.id)

    return redirect("events:organizer_dashboard")


@login_required
def verify_ticket(request, registration_id):
    """Verify a ticket from QR code scan (organizer or staff only)."""
    registration = get_object_or_404(Registration, pk=registration_id)
    event = registration.event
    
    if not (request.user.is_staff or event.organizer == request.user):
        messages.error(request, "You do not have permission to scan tickets for this event.")
        return redirect("events:event_detail", pk=event.pk)
    
    context = {
        "registration": registration,
        "event": event,
    }
    return render(request, "registrations/verify.html", context)


@login_required
def dashboard(request):
    """Show the user's active and past registrations."""
    confirmed = Registration.objects.filter(
        user=request.user, status="confirmed"
    ).select_related("event").prefetch_related("event__category")

    cancelled = Registration.objects.filter(
        user=request.user, status="cancelled"
    ).select_related("event")

    waitlist_entries = Waitlist.objects.filter(
        user=request.user
    ).select_related("event")

    context = {
        "confirmed_registrations": confirmed,
        "cancelled_registrations": cancelled,
        "waitlist_entries": waitlist_entries,
    }
    return render(request, "registrations/dashboard.html", context)
