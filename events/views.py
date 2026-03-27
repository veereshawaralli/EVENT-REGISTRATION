from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, UpdateView
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import csv
import logging

logger = logging.getLogger(__name__)

from .forms import EventForm, EventSearchForm
from .models import Category, Event, EventCommission


def event_list(request):
    """Homepage: list upcoming events with search, category filter, and pagination."""
    search_form = EventSearchForm(request.GET)
    queryset = Event.objects.filter(date__gte=timezone.now().date()).select_related("category")

    query = request.GET.get("q", "").strip()
    if query:
        queryset = queryset.filter(
            Q(title__icontains=query)
            | Q(location__icontains=query)
            | Q(description__icontains=query)
        )

    category_slug = request.GET.get("category", "").strip()
    active_category = None
    if category_slug:
        active_category = Category.objects.filter(slug=category_slug).first()
        if active_category:
            queryset = queryset.filter(category=active_category)

    tag_slug = request.GET.get("tag", "").strip()
    if tag_slug:
        queryset = queryset.filter(tags__slug=tag_slug)

    # Featured events (only on page 1 without active filters)
    featured_events = []
    if not query and not category_slug and request.GET.get("page") in (None, "1"):
        featured_events = Event.objects.filter(
            is_featured=True,
            date__gte=timezone.now().date(),
        ).select_related("category")[:3]

    categories = Category.objects.all()

    paginator = Paginator(queryset, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "search_form": search_form,
        "featured_events": featured_events,
        "query": query,
        "categories": categories,
        "active_category": active_category,
        "active_tag": tag_slug,
    }
    return render(request, "events/event_list.html", context)


def event_detail(request, pk):
    """Show full event details, registration status, reviews, and comments."""
    event = get_object_or_404(
        Event.objects.select_related("organizer", "category").prefetch_related("tags"),
        pk=pk
    )

    user_registered = False
    registration = None
    user_on_waitlist = False
    user_has_reviewed = False

    if request.user.is_authenticated:
        registration = event.registrations.filter(
            user=request.user, status="confirmed"
        ).first()
        user_registered = registration is not None
        user_on_waitlist = event.waitlist.filter(user=request.user).exists()
        user_has_reviewed = event.reviews.filter(user=request.user).exists()

    reviews = event.reviews.select_related("user").all()
    comments = event.comments.select_related("user").all()

    # Organizer: attendee list (for mark_attended view)
    attendee_list = None
    if request.user.is_authenticated and (
        request.user.is_staff or event.organizer == request.user
    ):
        attendee_list = event.registrations.filter(status="confirmed").select_related("user").prefetch_related("custom_values__field")

    context = {
        "event": event,
        "user_registered": user_registered,
        "registration": registration,
        "user_on_waitlist": user_on_waitlist,
        "user_has_reviewed": user_has_reviewed,
        "reviews": reviews,
        "comments": comments,
        "attendee_list": attendee_list,
    }
    return render(request, "events/event_detail.html", context)


@login_required
def organizer_dashboard(request):
    """Enhanced dashboard with revenue analytics and export options."""
    is_provider = getattr(request.user, 'profile', None) and request.user.profile.is_provider
    if not (request.user.is_staff or is_provider):
        messages.error(request, "This page is for event organizers only.")
        return redirect("events:event_list")

    if request.user.is_staff:
        my_events = Event.objects.all()
    else:
        my_events = Event.objects.filter(organizer=request.user)

    # Annotate with counts and revenue
    my_events = my_events.annotate(
        confirmed_count=Count("registrations", filter=Q(registrations__status="confirmed")),
        attended_count=Count("registrations", filter=Q(registrations__attended=True)),
        # Total revenue = sum of prices of all confirmed registrations
        # Note: Event.price is the unit price. Revenue = confirmed_count * price.
    ).order_by("-date")

    total_events = my_events.count()
    total_regs = 0
    total_attended = 0
    total_revenue = 0

    for e in my_events:
        total_regs += e.confirmed_count
        total_attended += e.attended_count
        total_revenue += e.confirmed_count * e.price

    # Chart.js data (last 10 events)
    recent_events = my_events[:10]
    chart_labels = [e.title[:15] for e in recent_events]
    chart_regs = [e.confirmed_count for e in recent_events]
    chart_attended = [e.attended_count for e in recent_events]
    chart_revenue = [float(e.confirmed_count * e.price) for e in recent_events]

    # Ensure EventCommission exists for each event
    for e in my_events:
        EventCommission.objects.get_or_create(event=e)

    context = {
        "my_events": my_events,
        "total_events": total_events,
        "total_regs": total_regs,
        "total_attended": total_attended,
        "total_revenue": total_revenue,
        "chart_labels": chart_labels,
        "chart_regs": chart_regs,
        "chart_attended": chart_attended,
        "chart_revenue": chart_revenue,
    }
    return render(request, "events/organizer_dashboard.html", context)


@login_required
def event_commission_checkout(request, event_id):
    """Render checkout for per-event commission payment."""
    event = get_object_or_404(Event, pk=event_id, organizer=request.user)
    commission = get_object_or_404(EventCommission, event=event)
    
    if commission.status == 'paid':
        messages.info(request, "Commission for this event is already paid.")
        return redirect("events:organizer_dashboard")

    amount_due = commission.commission_due
    amount_in_paise = int(amount_due * 100)
    
    razorpay_configured = bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET)
    razorpay_order_id = None
    
    if razorpay_configured and amount_in_paise > 0:
        try:
            import razorpay
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            
            order_data = {
                "amount": amount_in_paise,
                "currency": "INR",
                "receipt": f"evt_comm_{event.id}",
                "payment_capture": "1"
            }
            order = client.order.create(data=order_data)
            razorpay_order_id = order['id']
        except Exception as e:
            logger.error(f"Razorpay integration failed for event commission {event.id}: {e}")
            razorpay_configured = False

    context = {
        "event": event,
        "commission": commission,
        "amount": amount_in_paise,
        "display_amount": amount_due,
        "razorpay_order_id": razorpay_order_id,
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        "razorpay_configured": razorpay_configured,
    }
    return render(request, "events/event_commission_checkout.html", context)


@csrf_exempt
def event_commission_callback(request, event_id):
    """Callback for Razorpay to securely report event commission payment."""
    event = get_object_or_404(Event, pk=event_id)
    commission = get_object_or_404(EventCommission, event=event)

    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')

        try:
            import razorpay
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            })

            # Verification Successful
            commission.status = 'paid'
            commission.paid_at = timezone.now()
            commission.offline_payment_requested = False
            commission.save()

            messages.success(request, f"Commission for '{event.title}' paid successfully!")
            return redirect('events:organizer_dashboard')

        except Exception as e:
            logger.error(f"Event commission payment verification failed: {e}")
            messages.error(request, "Payment verification failed. Please contact support.")
            return redirect('events:organizer_dashboard')

    return redirect('events:organizer_dashboard')


@login_required
@require_POST
def event_commission_offline(request, event_id):
    """Handle request for offline event commission payment."""
    event = get_object_or_404(Event, pk=event_id, organizer=request.user)
    commission = get_object_or_404(EventCommission, event=event)
    
    if commission.status == 'paid':
        messages.info(request, "Commission already paid.")
        return redirect("events:organizer_dashboard")
        
    commission.offline_payment_requested = True
    commission.status = 'pending'
    commission.save()
    messages.success(request, f"Offline payment request sent for '{event.title}'. The admin will verify and update your status.")
    return redirect("events:organizer_dashboard")


@login_required
def export_attendees_csv(request, event_id):
    """Export the attendee list for a specific event as a CSV file."""
    event = get_object_or_404(Event, pk=event_id)
    if not (request.user.is_staff or event.organizer == request.user):
        messages.error(request, "You don't have permission to export this list.")
        return redirect("events:organizer_dashboard")

    registrations = event.registrations.filter(status="confirmed").select_related("user").prefetch_related("custom_values__field")
    custom_fields = event.custom_fields.all()

    response = HttpResponse(content_type='text/csv')
    filename = f"attendees_{event.title.replace(' ', '_')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    
    # Dynamic header
    header = ['Name', 'Email', 'Registration Date', 'Payment Status', 'Payment Method', 'Attended']
    for field in custom_fields:
        header.append(field.label)
    writer.writerow(header)

    for reg in registrations:
        row = [
            reg.user.get_full_name() or reg.user.username,
            reg.user.email,
            reg.registration_date.strftime('%Y-%m-%d %H:%M'),
            reg.payment_status,
            reg.get_payment_method_display(),
            'Yes' if reg.attended else 'No'
        ]
        
        # Add values for each custom field
        custom_values_map = {val.field_id: val.value for val in reg.custom_values.all()}
        for field in custom_fields:
            row.append(custom_values_map.get(field.id, ""))
            
        writer.writerow(row)

    return response


class EventCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new event (staff only)."""

    model = Event
    form_class = EventForm
    template_name = "events/event_form.html"

    def test_func(self):
        user = self.request.user
        is_provider = getattr(user, 'profile', None) and user.profile.is_provider
        return user.is_staff or is_provider

    def form_valid(self, form):
        form.instance.organizer = self.request.user
        response = super().form_valid(form)
        # Create corresponding commission record
        EventCommission.objects.get_or_create(event=self.object)
        messages.success(self.request, "Event created successfully!")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Create Event"
        context["submit_label"] = "Create Event"
        return context


class EventUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Edit an existing event (organizer or staff)."""

    model = Event
    form_class = EventForm
    template_name = "events/event_form.html"

    def test_func(self):
        event = self.get_object()
        user = self.request.user
        is_provider = getattr(user, 'profile', None) and user.profile.is_provider
        return user.is_staff or is_provider or event.organizer == user

    def form_valid(self, form):
        messages.success(self.request, "Event updated successfully!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Edit Event"
        context["submit_label"] = "Save Changes"
        return context


class EventDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete an event (organizer or staff)."""

    model = Event
    template_name = "events/event_confirm_delete.html"
    success_url = "/"

    def test_func(self):
        event = self.get_object()
        user = self.request.user
        is_provider = getattr(user, 'profile', None) and user.profile.is_provider
        return user.is_staff or is_provider or event.organizer == user

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Event deleted successfully.")
        return super().delete(request, *args, **kwargs)


@login_required
def qr_scanner(request):
    """
    Render the HTML5 QR Code Scanner page for organizers/staff to verify tickets.
    """
    is_provider = getattr(request.user, 'profile', None) and request.user.profile.is_provider
    if not (request.user.is_staff or is_provider):
        messages.error(request, "You do not have permission to access the scanner.")
        return redirect("events:event_list")
        
    return render(request, "events/scanner.html")


# ---------------------------------------------------------------------------
# Static / Policy Pages (Required for Razorpay Verification)
# ---------------------------------------------------------------------------

def about_us(request):
    return render(request, "events/policies/about.html")

def contact_us(request):
    return render(request, "events/policies/contact.html")

def privacy_policy(request):
    return render(request, "events/policies/privacy.html")

def terms_conditions(request):
    return render(request, "events/policies/terms.html")

def refund_policy(request):
    return render(request, "events/policies/refund.html")
