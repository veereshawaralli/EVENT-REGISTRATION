from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, UpdateView
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_sameorigin, xframe_options_exempt
from django.views.decorators.http import require_POST
import csv
import json
import logging
from decouple import config
import google.generativeai as genai

logger = logging.getLogger(__name__)

from .forms import EventForm, EventSearchForm, CertificateTemplateForm
from .models import Category, Event, EventCommission, CertificateTemplate


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
    else:
        # Increment view count for regular users/guests
        event.views += 1
        event.save(update_fields=['views'])

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
    """Enhanced dashboard with advanced analytics and charts."""
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
    ).order_by("-date")

    total_events = my_events.count()
    total_regs = 0
    total_attended = 0
    total_revenue = 0
    total_views = 0

    for e in my_events:
        total_regs += e.confirmed_count
        total_attended += e.attended_count
        total_revenue += e.confirmed_count * e.price
        total_views += e.views

    # Chart 1: Event Comparison (Registrations vs Attended vs Revenue)
    recent_events = my_events[:10]
    chart_labels = [e.title[:15] for e in recent_events]
    chart_regs = [e.confirmed_count for e in recent_events]
    chart_attended = [e.attended_count for e in recent_events]
    chart_revenue = [float(e.confirmed_count * e.price) for e in recent_events]
    
    # Chart 2: Conversion Rate (Views vs Registrations)
    conversion_rate = 0
    if total_views > 0:
        conversion_rate = round((total_regs / total_views) * 100, 1)

    # Chart 3: Sales Velocity (Registrations over time for all organizer events)
    from django.db.models.functions import TruncDate
    from registrations.models import Registration
    
    # Get registrations for the organizer's events
    sales_velocity_query = Registration.objects.filter(
        event__in=my_events, status="confirmed"
    ).annotate(
        day=TruncDate('registration_date')
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    # Format for Chart.js
    sales_velocity_labels = [entry['day'].strftime('%b %d') for entry in sales_velocity_query if entry['day']]
    sales_velocity_data = [entry['count'] for entry in sales_velocity_query]

    # Ensure EventCommission exists for each event
    for e in my_events:
        from .models import EventCommission
        EventCommission.objects.get_or_create(event=e)

    context = {
        "my_events": my_events,
        "total_events": total_events,
        "total_regs": total_regs,
        "total_attended": total_attended,
        "total_revenue": total_revenue,
        "total_views": total_views,
        "conversion_rate": conversion_rate,
        "chart_labels": chart_labels,
        "chart_regs": chart_regs,
        "chart_attended": chart_attended,
        "chart_revenue": chart_revenue,
        "sales_velocity_labels": sales_velocity_labels,
        "sales_velocity_data": sales_velocity_data,
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

@login_required
@require_POST
def ai_generate_event_content(request):
    """Generate event content using Gemini API from a prompt."""
    try:
        data = json.loads(request.body)
        prompt = data.get("prompt", "").strip()
        
        if not prompt:
            return JsonResponse({"error": "Prompt is required."}, status=400)
            
        api_key = config("GEMINI_API_KEY", default="").strip(' "\'')
        if not api_key:
            return JsonResponse({"error": "AI not configured on server."}, status=500)
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        system_prompt = """
        You are an AI event content generator. The user will provide a rough idea.
        You must return ONLY a valid JSON object (without markdown blocks) containing exactly:
        {
            "title": "A catchy, professional title",
            "description": "A detailed, engaging description (plain text with line breaks \\n, no markdown bold/italics)",
            "location": "Suggested location (if implied, else empty)",
            "tags": "3-5 relevant comma-separated tags"
        }
        """
        
        response = model.generate_content(f"{system_prompt}\nUser Idea: {prompt}")
        
        text_response = response.text.strip()
        if text_response.startswith("```json"):
            text_response = text_response.replace("```json", "").replace("```", "").strip()
        elif text_response.startswith("```"):
            text_response = text_response.replace("```", "").strip()
            
        parsed_data = json.loads(text_response)
        
        return JsonResponse({
            "title": parsed_data.get("title", ""),
            "description": parsed_data.get("description", ""),
            "location": parsed_data.get("location", ""),
            "tags": parsed_data.get("tags", "")
        })
        
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request format or AI response format."}, status=400)
    except Exception as e:
        logger.error(f"AI Generation failed: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def certificate_builder(request, event_id):
    """View to customize the certificate for an event."""
    event = get_object_or_404(Event, pk=event_id)
    
    # Only allow organizer or staff
    is_provider = getattr(request.user, 'profile', None) and request.user.profile.is_provider
    if not (request.user.is_staff or is_provider or request.user == event.organizer):
        messages.error(request, "You do not have permission to edit this event's certificate.")
        return redirect("events:event_list")

    # Get or create template
    template, created = CertificateTemplate.objects.get_or_create(event=event)

    if request.method == "POST":
        form = CertificateTemplateForm(request.POST, request.FILES, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, "Certificate template updated successfully.")
            return redirect("events:certificate_builder", event_id=event.id)
    else:
        form = CertificateTemplateForm(instance=template)

    context = {
        "event": event,
        "form": form,
        "template": template,
    }
    return render(request, "events/certificate_builder.html", context)


@login_required
def certificate_preview(request, event_id):
    """Renders the dual-preview page (HTML + PDF iframe)."""
    event = get_object_or_404(Event, pk=event_id)
    
    is_provider = getattr(request.user, 'profile', None) and request.user.profile.is_provider
    if not (request.user.is_staff or is_provider or request.user == event.organizer):
        messages.error(request, "Unauthorized")
        return redirect("events:event_list")

    template, _ = CertificateTemplate.objects.get_or_create(event=event)
    
    # Process layout for HTML preview
    layout = template.layout or {
        'title': { 'x': 50, 'y': 15, 'text': "CERTIFICATE", 'font_size': 48, 'color': "#1a2f4c", 'weight': "bold" },
        'subtitle': { 'x': 50, 'y': 28, 'text': "Of Achievement", 'font_size': 20, 'color': "#d4af37", 'weight': "normal" },
        'name': { 'x': 50, 'y': 45, 'text': "Jane Doe", 'font_size': 36, 'color': "#1a2f4c", 'weight': "normal" },
        'description': { 'x': 50, 'y': 65, 'text': f"Proudly presented for attending {event.title}", 'font_size': 16, 'color': "#555555", 'weight': "normal" },
        'date': { 'x': 20, 'y': 85, 'text': "Issued: June 29, 2026", 'font_size': 14, 'color': "#1a2f4c", 'weight': "normal" },
        'signature': { 'x': 80, 'y': 85, 'text': event.organizer.get_full_name() or event.organizer.username, 'font_size': 14, 'color': "#1a2f4c", 'weight': "normal" }
    }
    
    # Replace placeholders in layout for HTML preview
    for key, config in layout.items():
        if 'text' in config:
            config['text'] = config['text'].replace('[Attendee Name]', "Jane Doe")
            config['text'] = config['text'].replace('[Date]', "June 29, 2026")
            config['text'] = config['text'].replace('[Signature]', event.organizer.get_full_name() or event.organizer.username)

    context = {
        "event": event,
        "template": template,
        "layout": layout
    }
    return render(request, "events/certificate_preview.html", context)


@login_required
@xframe_options_exempt
def certificate_preview_pdf(request, event_id):
    """Generates a raw PDF preview of the certificate."""
    event = get_object_or_404(Event, pk=event_id)
    
    is_provider = getattr(request.user, 'profile', None) and request.user.profile.is_provider
    if not (request.user.is_staff or is_provider or request.user == event.organizer):
        return HttpResponse("Unauthorized", status=401)

    # Mock registration for preview
    class DummyUser:
        def get_full_name(self):
            return "Jane Doe"
        username = "janedoe"
        email = "jane@example.com"

    class DummyRegistration:
        def __init__(self, evt):
            self.user = DummyUser()
            self.event = evt
            self.attended = True

    dummy_reg = DummyRegistration(event)
    
    try:
        from registrations.utils import generate_certificate_pdf
        pdf_bytes = generate_certificate_pdf(dummy_reg)
        
        if pdf_bytes:
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = 'inline; filename="preview.pdf"'
            return response
        else:
            logger.error(f"Certificate PDF generation failed for event {event_id} (Preview). Check registrations/utils.py logs.")
            return HttpResponse("Error generating PDF preview. Please check if the background image and layout are valid.", status=500)
    except Exception as e:
        import traceback
        logger.error(f"Exception during certificate preview PDF for event {event_id}: {e}\n{traceback.format_exc()}")
        return HttpResponse(f"Internal Error: {str(e)}", status=500)


@login_required
@require_POST
def send_certificate_manual(request, registration_id):
    """Manually trigger certificate generation and email for a specific attendee."""
    from registrations.models import Registration
    registration = get_object_or_404(Registration, pk=registration_id)
    event = registration.event
    
    if not (request.user.is_staff or event.organizer == request.user):
        messages.error(request, "You do not have permission to send certificates for this event.")
        return redirect("events:event_detail", pk=event.pk)
    
    if not registration.attended:
        messages.error(request, "Cannot send certificate to an attendee who hasn't checked in yet.")
        return redirect("events:event_detail", pk=event.pk)

    try:
        from registrations.utils import generate_certificate_pdf
        from registrations.emails import send_certificate_email
        
        pdf_buffer = generate_certificate_pdf(registration)
        if pdf_buffer:
            send_certificate_email(registration, pdf_buffer)
            messages.success(request, f"Certificate manually sent to {registration.user.email}.")
        else:
            messages.error(request, "Failed to generate the PDF certificate.")
    except Exception as e:
        logger.error(f"Manual certificate send failed: {e}")
        messages.error(request, f"Error sending certificate: {str(e)}")
        
    return redirect("events:event_detail", pk=event.pk)

