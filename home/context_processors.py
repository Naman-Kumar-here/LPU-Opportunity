from .models import Notification, Message


def notification_context(request):

    if request.user.is_authenticated:

        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()

        messages_unread_count = Message.objects.filter(
            conversation__status="active",
            is_read=False
        ).exclude(
            sender=request.user
        ).filter(
            conversation__creator=request.user
        ).count()

        messages_unread_count += Message.objects.filter(
            conversation__status="active",
            is_read=False
        ).exclude(
            sender=request.user
        ).filter(
            conversation__applicant=request.user
        ).count()

        latest_notifications = Notification.objects.filter(
            user=request.user
        ).order_by("-created_at")[:5]

        return {
            "unread_count": unread_count,
            "messages_unread_count": messages_unread_count,
            "latest_notifications": latest_notifications,
        }

    return {
        "unread_count": 0,
        "messages_unread_count": 0,
        "latest_notifications": [],
    }