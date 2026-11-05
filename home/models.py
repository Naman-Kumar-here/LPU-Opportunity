from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    student_id = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True
    )

    phone_number = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True
    )

    email = models.EmailField(
        unique=True,
        null=True,
        blank=True
    )

    email_verified = models.BooleanField(default=False)

    notifications_enabled = models.BooleanField(default=True)

    email_otp = models.CharField(
        max_length=6,
        blank=True,
        null=True
    )

    otp_created_at = models.DateTimeField(
        blank=True,
        null=True
    )

    otp_attempts = models.IntegerField(default=0)

    course = models.CharField(
    max_length=100,
    blank=True
    )

    year = models.CharField(
    max_length=30,
    blank=True
    )

    specialization = models.CharField(
    max_length=100,
    blank=True
    )

    skills = models.CharField(
    max_length=300,
    blank=True
    )

    bio = models.TextField(blank=True)

    def __str__(self):
        return self.user.username

class Opportunity(models.Model):

    CATEGORY_CHOICES = [
        ("hackathon", "Hackathon"),
        ("research", "Research"),
        ("internship", "Internship"),
        ("workshop", "Workshop"),
        ("competition", "Competition"),
        ("event", "Event"),
        ("project", "Project"),
        ("club", "Club / Society"),
        ("volunteering", "Volunteering"),
        ("other", "Other"),
    ]

    posted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="other"
    )
    students_needed = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    member_left = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class Application(models.Model):
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE)
    applicant = models.ForeignKey(User, on_delete=models.CASCADE)

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("left", "Left"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    applied_at = models.DateTimeField(auto_now_add=True)

class Notification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    message = models.TextField()

    opportunity = models.ForeignKey(
        Opportunity,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    notification_type = models.CharField(
    max_length=20,
    default="general"
    )

    is_read = models.BooleanField(default=False)

    urgent_notification_sent = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.message}"

class Conversation(models.Model):
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE)

    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_conversations"
    )

    applicant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="applicant_conversations"
    )

    status = models.CharField(
        max_length=10,
        choices=[
            ("active", "Active"),
            ("ended", "Ended"),
        ],
        default="active"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.opportunity.title} - {self.creator.username} & {self.applicant.username}"


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username}: {self.content[:30]}"


