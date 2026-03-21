from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, UpdateView

from .forms import EventForm, EventSearchForm
from .models import Category, Event


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
        attendee_list = event.registrations.filter(status="confirmed").select_related("user")

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
    """Stats dashboard for organizers/staff."""
    if not (request.user.is_staff or request.user.organized_events.exists()):
        messages.error(request, "This page is for event organizers only.")
        return redirect("events:event_list")

    if request.user.is_staff:
        my_events = Event.objects.all()
    else:
        my_events = Event.objects.filter(organizer=request.user)

    my_events = my_events.annotate(
        confirmed_count=Count("registrations", filter=Q(registrations__status="confirmed")),
        attended_count=Count("registrations", filter=Q(registrations__attended=True)),
    ).order_by("-date")

    total_events = my_events.count()
    total_regs = sum(e.confirmed_count for e in my_events)
    total_attended = sum(e.attended_count for e in my_events)

    # Chart.js data
    chart_labels = [e.title[:20] for e in my_events[:10]]
    chart_regs = [e.confirmed_count for e in my_events[:10]]
    chart_attended = [e.attended_count for e in my_events[:10]]

    context = {
        "my_events": my_events,
        "total_events": total_events,
        "total_regs": total_regs,
        "total_attended": total_attended,
        "chart_labels": chart_labels,
        "chart_regs": chart_regs,
        "chart_attended": chart_attended,
    }
    return render(request, "events/organizer_dashboard.html", context)


class EventCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new event (staff only)."""

    model = Event
    form_class = EventForm
    template_name = "events/event_form.html"

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        form.instance.organizer = self.request.user
        messages.success(self.request, "Event created successfully!")
        return super().form_valid(form)

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
        return user.is_staff or event.organizer == user

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
        return user.is_staff or event.organizer == user

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Event deleted successfully.")
        return super().delete(request, *args, **kwargs)


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
