from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from events.models import Event

from .models import Comment


@login_required
def add_comment(request, event_pk):
    """Add a comment/question on an event."""
    event = get_object_or_404(Event, pk=event_pk)

    if request.method != "POST":
        return redirect("events:event_detail", pk=event_pk)

    body = request.POST.get("body", "").strip()
    if not body:
        messages.error(request, "Comment cannot be empty.")
        return redirect("events:event_detail", pk=event_pk)

    Comment.objects.create(user=request.user, event=event, body=body)
    messages.success(request, "Comment posted!")
    return redirect("events:event_detail", pk=event_pk)


@login_required
def delete_comment(request, comment_pk):
    """Delete own comment (or staff)."""
    comment = get_object_or_404(Comment, pk=comment_pk)
    if request.user != comment.user and not request.user.is_staff:
        messages.error(request, "You cannot delete this comment.")
        return redirect("events:event_detail", pk=comment.event.pk)

    event_pk = comment.event.pk
    if request.method == "POST":
        comment.delete()
        messages.success(request, "Comment deleted.")
    return redirect("events:event_detail", pk=event_pk)
