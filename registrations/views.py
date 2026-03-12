from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render

from events.models import Event

from .models import Registration


@login_required
def register_for_event(request, event_id):
    """Register the current user for an event."""
    event = get_object_or_404(Event, pk=event_id)

    if request.method != "POST":
        return redirect("events:event_detail", pk=event_id)

    # Check if event is full
    if event.is_full:
        messages.error(request, "Sorry, this event is fully booked.")
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

    # Check for a previously cancelled registration and reactivate it
    cancelled_reg = Registration.objects.filter(
        user=request.user, event=event, status="cancelled"
    ).first()
    if cancelled_reg:
        cancelled_reg.status = "confirmed"
        cancelled_reg.save()
        messages.success(request, f"You have been re-registered for {event.title}!")
        return redirect("events:event_detail", pk=event_id)

    # Create new registration
    try:
        Registration.objects.create(user=request.user, event=event, status="confirmed")
        messages.success(request, f"Successfully registered for {event.title}!")
    except IntegrityError:
        messages.error(request, "Registration failed. Please try again.")

    return redirect("events:event_detail", pk=event_id)


@login_required
def cancel_registration(request, registration_id):
    """Cancel an existing registration."""
    registration = get_object_or_404(
        Registration, pk=registration_id, user=request.user, status="confirmed"
    )

    if request.method == "POST":
        registration.status = "cancelled"
        registration.save()
        messages.success(
            request,
            f"Your registration for {registration.event.title} has been cancelled.",
        )

    return redirect("registrations:dashboard")


@login_required
def dashboard(request):
    """Show the user's active and past registrations."""
    confirmed = Registration.objects.filter(
        user=request.user, status="confirmed"
    ).select_related("event")

    cancelled = Registration.objects.filter(
        user=request.user, status="cancelled"
    ).select_related("event")

    context = {
        "confirmed_registrations": confirmed,
        "cancelled_registrations": cancelled,
    }
    return render(request, "registrations/dashboard.html", context)
