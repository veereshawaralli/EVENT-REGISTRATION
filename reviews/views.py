from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from events.models import Event
from registrations.models import Registration

from .models import Review


@login_required
def submit_review(request, event_pk):
    """Submit or update a review for an event (attendees-only)."""
    event = get_object_or_404(Event, pk=event_pk)

    if request.method != "POST":
        return redirect("events:event_detail", pk=event_pk)

    # Check the user actually attended
    attended = Registration.objects.filter(
        user=request.user, event=event, attended=True
    ).exists()
    if not attended:
        messages.error(request, "Only verified attendees can leave a review.")
        return redirect("events:event_detail", pk=event_pk)

    # Check for existing review
    if Review.objects.filter(user=request.user, event=event).exists():
        messages.warning(request, "You have already reviewed this event.")
        return redirect("events:event_detail", pk=event_pk)

    rating = request.POST.get("rating")
    comment = request.POST.get("comment", "").strip()

    if not rating or not rating.isdigit() or not (1 <= int(rating) <= 5):
        messages.error(request, "Please select a valid rating (1–5 stars).")
        return redirect("events:event_detail", pk=event_pk)

    Review.objects.create(
        user=request.user, event=event, rating=int(rating), comment=comment
    )
    messages.success(request, "Thank you for your review!")
    return redirect("events:event_detail", pk=event_pk)


@login_required
def delete_review(request, review_pk):
    """Delete own review (or staff)."""
    review = get_object_or_404(Review, pk=review_pk)
    if request.user != review.user and not request.user.is_staff:
        messages.error(request, "You cannot delete this review.")
        return redirect("events:event_detail", pk=review.event.pk)

    event_pk = review.event.pk
    if request.method == "POST":
        review.delete()
        messages.success(request, "Review deleted.")
    return redirect("events:event_detail", pk=event_pk)
