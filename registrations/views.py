# import razorpay (moved inside functions)
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

from events.models import Event
from .models import Registration, Waitlist
from .emails import send_registration_confirmation, send_waitlist_promotion


def _send_registration_email(user, event, action="registered", registration=None):
    """
    Deprecated: Using rich HTML emails from .emails instead.
    Refactored to call the new helpers for backward compatibility where possible.
    """
    if action == "registered" and registration:
        send_registration_confirmation(registration)
    elif action == "promoted":
        send_waitlist_promotion(user, event)
    else:
        # Fallback for simple actions or missing registration object
        subject_map = {
            "cancelled": f"❌ Cancelled: {event.title}",
            "waitlisted": f"⏳ Waitlisted: {event.title}",
        }
        body_map = {
            "cancelled": f"Hi {user.first_name or user.username},\n\nYour registration for {event.title} has been cancelled.",
            "waitlisted": f"Hi {user.first_name or user.username},\n\n{event.title} is full. You've been added to the waitlist.",
        }
        try:
            send_mail(
                subject=subject_map.get(action, "EventHub Notification"),
                message=body_map.get(action, "Notification from EventHub"),
                from_email=None,
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
        user=request.user, event=event
    ).first()
    
    if existing:
        if existing.status == "confirmed":
            messages.warning(request, "You are already registered for this event.")
            return redirect("events:event_detail", pk=event_id)
        elif existing.status == "pending":
            return redirect("registrations:checkout", registration_id=existing.id)

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
        if event.is_free:
        cancelled_reg.status = "confirmed"
        cancelled_reg.payment_status = "completed"
        cancelled_reg.save()
        _send_registration_email(request.user, event, action="registered", registration=cancelled_reg)
        messages.success(request, f"You have been re-registered for {event.title}!")
            return redirect("events:event_detail", pk=event_id)
        else:
            cancelled_reg.status = "pending"
            cancelled_reg.payment_status = "pending"
            cancelled_reg.save()
            return redirect("registrations:checkout", registration_id=cancelled_reg.id)

    # Create new registration
    try:
        registration = Registration.objects.create(
            user=request.user, 
            event=event, 
            status="confirmed" if event.is_free else "pending",
            payment_status="completed" if event.is_free else "pending"
        )
        if event.is_free:
            _send_registration_email(request.user, event, action="registered", registration=registration)
            messages.success(request, f"Successfully registered for {event.title}!")
            return redirect("events:event_detail", pk=event_id)
        else:
            return redirect("registrations:checkout", registration_id=registration.id)
    except IntegrityError:
        messages.error(request, "Registration failed. Please try again.")
    except Exception as e:
        logger.exception(f"Unexpected error during registration of user {request.user.id} for event {event_id}: {e}")
        messages.error(request, "An internal server error occurred. Please try again later.")

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
        next_waiter = Waitlist.objects.filter(event=registration.event).order_by('joined_at').first()
        if next_waiter:
            _send_registration_email(next_waiter.user, registration.event, action="promoted")
            # Note: We don't delete from waitlist until they actually register or we automate it.
            # For now, we just notify them.

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

    pending_payments = Registration.objects.filter(
        user=request.user, status="pending"
    ).select_related("event")

    context = {
        "confirmed_registrations": confirmed,
        "cancelled_registrations": cancelled,
        "waitlist_entries": waitlist_entries,
        "pending_payments": pending_payments,
    }
    return render(request, "registrations/dashboard.html", context)


@login_required
def payment_checkout(request, registration_id):
    """Render checkout page and configure Razorpay SDK if available."""
    registration = get_object_or_404(
        Registration, pk=registration_id, user=request.user, status="pending"
    )
    event = registration.event
    amount_in_paise = int(event.price * 100)

    razorpay_configured = bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET)
    
    if razorpay_configured:
        try:
            import razorpay
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            
            # Generate a Razorpay order if we don't have one yet
            if not registration.razorpay_order_id:
                order_data = {
                    "amount": amount_in_paise,
                    "currency": "INR",
                    "receipt": f"reg_{registration.id}",
                    "payment_capture": "1"
                }
                order = client.order.create(data=order_data)
                registration.razorpay_order_id = order['id']
                registration.save(update_fields=['razorpay_order_id'])
        except Exception as e:
            logger.error(f"Razorpay integration failed: {e}")
            razorpay_configured = False

    context = {
        "registration": registration,
        "event": event,
        "razorpay_order_id": registration.razorpay_order_id,
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        "amount": amount_in_paise,
        "razorpay_configured": razorpay_configured,
    }
    return render(request, "registrations/checkout.html", context)


@csrf_exempt
def payment_callback(request):
    """Callback for Razorpay to securely report a payment transaction."""
    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')

        registration = get_object_or_404(Registration, razorpay_order_id=razorpay_order_id)
        
        # Payment must be pending
        if registration.status == "confirmed":
            return redirect('registrations:dashboard')

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        try:
            # Cryptographically verify the signature
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            })

            # Verification Successful
            registration.payment_status = "completed"
            registration.status = "confirmed"
            registration.razorpay_payment_id = payment_id
            registration.save()

            _send_registration_email(registration.user, registration.event, action="registered", registration=registration)
            messages.success(request, f"Payment successful! You are successfully registered for {registration.event.title}.")
            return redirect('registrations:dashboard')

        except razorpay.errors.SignatureVerificationError:
            # Verification Failed
            registration.payment_status = "failed"
            registration.save(update_fields=['payment_status'])
            messages.error(request, "Payment signature verification failed. The transaction was aborted.")
            return redirect('events:event_detail', pk=registration.event.id)

    return redirect('events:event_list')

@login_required
@require_POST
def process_offline_payment(request, registration_id):
    """Process an 'offline' (Pay at Venue) payment choice."""
    try:
        registration = get_object_or_404(
            Registration, pk=registration_id, user=request.user, status="pending"
        )
        
        # Update registration to reflect offline choice
        registration.payment_method = "offline"
        registration.status = "confirmed"  # Confirm the ticket so they receive it
        # We deliberately leave payment_status as "pending" since they need to pay at venue
        registration.save()
        
        # Send email containing the ticket/QR code
        _send_registration_email(registration.user, registration.event, action="registered", registration=registration)
        messages.success(request, f"Your spot for {registration.event.title} is reserved! Please pay at the venue.")
        
        return redirect('registrations:dashboard')
    except Exception as e:
        logger.exception(f"Error processing offline payment for registration {registration_id}: {e}")
        messages.error(request, "An internal error occurred while processing your offline payment. Please try again.")
        return redirect('registrations:checkout', registration_id=registration_id)
