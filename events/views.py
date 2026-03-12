from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, UpdateView

from .forms import EventForm, EventSearchForm
from .models import Event


def event_list(request):
    """
    Homepage: list all upcoming events with search and pagination.
    Featured events are shown in a separate section.
    """
    search_form = EventSearchForm(request.GET)
    queryset = Event.objects.filter(date__gte=timezone.now().date())

    query = request.GET.get("q", "").strip()
    if query:
        queryset = queryset.filter(
            Q(title__icontains=query)
            | Q(location__icontains=query)
            | Q(description__icontains=query)
        )

    # Featured events (only on the first page without search)
    featured_events = []
    if not query and request.GET.get("page") in (None, "1"):
        featured_events = Event.objects.filter(
            is_featured=True,
            date__gte=timezone.now().date(),
        )[:3]

    paginator = Paginator(queryset, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "search_form": search_form,
        "featured_events": featured_events,
        "query": query,
    }
    return render(request, "events/event_list.html", context)


def event_detail(request, pk):
    """Show full event details and registration status."""
    event = get_object_or_404(Event, pk=pk)

    user_registered = False
    registration = None
    if request.user.is_authenticated:
        registration = event.registrations.filter(
            user=request.user, status="confirmed"
        ).first()
        user_registered = registration is not None

    context = {
        "event": event,
        "user_registered": user_registered,
        "registration": registration,
    }
    return render(request, "events/event_detail.html", context)


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
