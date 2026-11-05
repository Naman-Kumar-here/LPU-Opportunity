from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse

from .models import Opportunity, Application, Profile, Notification, Conversation, Message
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

# Email verification
from django.core.mail import send_mail
import secrets
from django.utils import timezone


# Create your views here.

# Registration (start) :-
def register_user(request):

    if request.method == "POST":

        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        email = request.POST.get("email", "").strip()
        phone_number = request.POST.get("phone_number", "").strip()
        student_id = request.POST.get("student_id", "").strip()


        # Check if username already exists
        existing_user = User.objects.filter(
            username=username
        ).first()


        # If username exists
        if existing_user:

            existing_profile = Profile.objects.filter(
                user=existing_user
            ).first()

            # Verified account cannot be registered again
            if existing_profile and existing_profile.email_verified:
                messages.error(
                    request,
                    "Username already exists"
                )
                return redirect("register")

            # Unverified account can try registration again
            if existing_profile and not existing_profile.email_verified:

                # Check whether email belongs to another account
                email_used = Profile.objects.filter(
                    email=email
                ).exclude(
                    user=existing_user
                ).exists()

                if email_used:
                    messages.error(
                        request,
                        "Email already registered"
                    )
                    return redirect("register")

                # Check phone number
                phone_used = Profile.objects.filter(
                    phone_number=phone_number
                ).exclude(
                    user=existing_user
                ).exists()

                if phone_used:
                    messages.error(
                        request,
                        "Phone number already registered"
                    )
                    return redirect("register")

                # Check student ID
                student_id_used = Profile.objects.filter(
                    student_id=student_id
                ).exclude(
                    user=existing_user
                ).exists()

                if student_id_used:
                    messages.error(
                        request,
                        "Student ID already registered"
                    )
                    return redirect("register")

                # Generate new OTP
                otp = str(
                    secrets.randbelow(900000) + 100000
                )

                # Update existing unverified profile
                existing_profile.email = email
                existing_profile.phone_number = phone_number
                existing_profile.student_id = student_id
                existing_profile.email_verified = False
                existing_profile.email_otp = otp
                existing_profile.otp_created_at = timezone.now()
                existing_profile.otp_attempts = 0
                existing_profile.save()

                # Update password
                existing_user.set_password(password)
                existing_user.save()

                # Save email in session
                request.session["verification_email"] = email

                # Send new OTP
                send_mail(
                    subject="LPU Opportunities - Email Verification",

                    message=f"""
Hello {username},

Welcome to LPU Opportunities!

Your new email verification OTP is:

{otp}

This OTP is valid for 10 minutes.

If you did not create this account, please ignore this email.

Thanks,
LPU Opportunities
""",

                    from_email="lpuopportunity67@gmail.com",

                    recipient_list=[email],

                    fail_silently=False,
                )

                messages.success(
                    request,
                    "A new OTP has been sent to your email."
                )

                return redirect("verify_otp")


        # Email already exists
        if Profile.objects.filter(
            email=email
        ).exists():

            messages.error(
                request,
                "Email already registered"
            )
            return redirect("register")


        # Phone number already exists
        if Profile.objects.filter(
            phone_number=phone_number
        ).exists():

            messages.error(
                request,
                "Phone number already registered"
            )
            return redirect("register")


        # Student ID already exists
        if Profile.objects.filter(
            student_id=student_id
        ).exists():

            messages.error(
                request,
                "Student ID already registered"
            )
            return redirect("register")


        # Create User
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )


        # Generate 6-digit secret OTP
        otp = str(
            secrets.randbelow(900000) + 100000
        )


        # Save email in session
        request.session["verification_email"] = email


        # Create Profile
        Profile.objects.create(
            user=user,
            email=email,
            phone_number=phone_number,
            student_id=student_id,
            email_verified=False,
            email_otp=otp,
            otp_created_at=timezone.now(),
            otp_attempts=0
        )


        # Send OTP email
        send_mail(
            subject="LPU Opportunities - Email Verification",

            message=f"""
Hello {username},

Welcome to LPU Opportunities!

Your email verification OTP is:

{otp}

This OTP is valid for 10 minutes.

If you did not create this account, please ignore this email.

Thanks,
LPU Opportunities
""",

            from_email="lpuopportunity67@gmail.com",

            recipient_list=[email],

            fail_silently=False,
        )


        messages.success(
            request,
            "Account created! Please check your email for the verification OTP."
        )

        return redirect("verify_otp")


    return render(request, "register.html")
# Registration (end) :-


# OTP Verification
def verify_otp(request):

    email = request.session.get("verification_email")

    if not email:
        messages.error(
            request,
            "Verification session expired. Please register again."
        )
        return redirect("register")

    try:
        profile = Profile.objects.get(email=email)

    except Profile.DoesNotExist:
        messages.error(request, "Account not found.")
        return redirect("register")


    # Already verified
    if profile.email_verified:
        request.session.pop("verification_email", None)

        messages.success(
            request,
            "Email is already verified. You can login."
        )

        return redirect("login")


    if request.method == "POST":

        otp = request.POST.get("otp")


        # OTP attempts limit
        if profile.otp_attempts >= 5:
            messages.error(
                request,
                "Too many wrong attempts. Please request a new OTP."
            )
            return redirect("verify_otp")


        # OTP expiry
        if profile.otp_created_at:

            time_difference = (
                timezone.now() - profile.otp_created_at
            )

            if time_difference.total_seconds() > 600:

                messages.error(
                    request,
                    "OTP has expired. Please request a new OTP."
                )

                return redirect("verify_otp")


        # Correct OTP
        if profile.email_otp == otp:

            profile.email_verified = True
            profile.email_otp = None
            profile.otp_created_at = None
            profile.otp_attempts = 0
            profile.save()

            # Remove email from session
            request.session.pop("verification_email", None)

            messages.success(
                request,
                "Email verified successfully! You can now login."
            )

            return redirect("login")


        # Wrong OTP
        profile.otp_attempts += 1
        profile.save()

        messages.error(
            request,
            "Invalid OTP. Please try again."
        )


    return render(request, "verify_otp.html")


# Login (start) :-
def login_user(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            profile = Profile.objects.get(user=user)

            # Email verification check
            if not profile.email_verified:

                messages.error(
                    request,
                    "Please verify your email before logging in."
                )

                return redirect("login")

            login(request, user)

            # Profile completion check
            if not (
                profile.course
                and profile.year
                and profile.specialization
                and profile.skills
                and profile.bio
            ):
                return redirect("edit_profile")

            return redirect("home")

        messages.error(
            request,
            "Invalid username or password"
        )

    return render(request, "login.html")


# Login (end) :-

# Logout 
@login_required
def logout_user(request):

    if request.method != "POST":
        return redirect("home")

    logout(request)

    return redirect("login")

# homepage :-
@login_required
def home(request):

    search_query = request.GET.get("search", "").strip()
    selected_category = request.GET.get("category", "")
    selected_sort = request.GET.get("sort", "newest")

    opportunities = Opportunity.objects.all()

    # Search
    if search_query:
        opportunities = opportunities.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Category Filter
    if selected_category:
        opportunities = opportunities.filter(
            category=selected_category
        )

    # Default sorting
    opportunities = opportunities.order_by("-created_at")

    available_opportunities = []

    for opportunity in opportunities:

        accepted_count = Application.objects.filter(
            opportunity=opportunity,
            status="accepted"
        ).count()

        available_seats = opportunity.students_needed - accepted_count

        # Only show opportunities where seats are available
        if available_seats > 0:

            opportunity.accepted_count = accepted_count
            opportunity.available_seats = available_seats

            available_opportunities.append(opportunity)

    # Sorting
    if selected_sort == "oldest":
        available_opportunities.sort(
            key=lambda x: x.created_at
        )

    elif selected_sort == "students_high":
        available_opportunities.sort(
            key=lambda x: x.students_needed,
            reverse=True
        )

    elif selected_sort == "students_low":
        available_opportunities.sort(
            key=lambda x: x.students_needed
        )

    elif selected_sort == "seats_high":
        available_opportunities.sort(
            key=lambda x: x.available_seats,
            reverse=True
        )

    elif selected_sort == "seats_low":
        available_opportunities.sort(
            key=lambda x: x.available_seats
        )

    return render(request, "home.html", {
        "opportunities": available_opportunities,
        "search_query": search_query,
        "selected_category": selected_category,
        "selected_sort": selected_sort,
    })

# create oppurtunity :- 

@login_required
def create_opportunity(request):

    if request.method == "POST":

        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        category = request.POST.get("category", "").strip()
        students_needed = request.POST.get("students_needed", "").strip()

        # Title blank nahi hona chahiye
        if not title:
            messages.error(request, "Opportunity title is required.")
            return render(request, "create_opportunity.html")

        # Category valid honi chahiye
        valid_categories = dict(Opportunity.CATEGORY_CHOICES)

        if category not in valid_categories:
            messages.error(request, "Please select a valid category.")
            return render(request, "create_opportunity.html")

        # Students needed valid positive number hona chahiye
        try:
            students_needed = int(students_needed)
        except (ValueError, TypeError):
            messages.error(request, "Please enter a valid number of students.")
            return render(request, "create_opportunity.html")

        if students_needed <= 0:
            messages.error(request, "Students needed must be at least 1.")
            return render(request, "create_opportunity.html")

        Opportunity.objects.create(
            posted_by=request.user,
            title=title,
            description=description,
            category=category,
            students_needed=students_needed
        )

        messages.success(
            request,
            "Opportunity created successfully!"
        )

        return redirect("home")

    return render(request, "create_opportunity.html")


# opportunity detail
@login_required
def opportunity_detail(request, id):
    opportunity = get_object_or_404(Opportunity, id=id)

    accepted_count = Application.objects.filter(
        opportunity=opportunity,
        status="accepted"
    ).count()

    available_seats = opportunity.students_needed - accepted_count

    return render(request, "opportunity_detail.html", {
        "opportunity": opportunity,
        "accepted_count": accepted_count,
        "available_seats": available_seats,
    })

# edit opportunity
@login_required
def edit_opportunity(request, id):

    opportunity = get_object_or_404(Opportunity, id=id)

    # Only the owner can edit
    if opportunity.posted_by != request.user:
        messages.error(
            request,
            "You are not allowed to edit this opportunity."
        )
        return redirect("opportunity_detail", id=opportunity.id)

    # Only POST can update the opportunity
    if request.method == "POST":

        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        category = request.POST.get("category", "").strip()
        students_needed = request.POST.get("students_needed", "").strip()

        # Title blank nahi hona chahiye
        if not title:
            messages.error(request, "Opportunity title is required.")
            return render(
                request,
                "edit_opportunity.html",
                {"opportunity": opportunity}
            )

        # Category valid honi chahiye
        valid_categories = dict(Opportunity.CATEGORY_CHOICES)

        if category not in valid_categories:
            messages.error(request, "Please select a valid category.")
            return render(
                request,
                "edit_opportunity.html",
                {"opportunity": opportunity}
            )

        # Students needed valid positive number hona chahiye
        try:
            students_needed = int(students_needed)
        except (ValueError, TypeError):
            messages.error(request, "Please enter a valid number of students.")
            return render(
                request,
                "edit_opportunity.html",
                {"opportunity": opportunity}
            )

        if students_needed <= 0:
            messages.error(request, "Students needed must be at least 1.")
            return render(
                request,
                "edit_opportunity.html",
                {"opportunity": opportunity}
            )

        opportunity.title = title
        opportunity.description = description
        opportunity.category = category
        opportunity.students_needed = students_needed

        opportunity.save()

        messages.success(
            request,
            "Opportunity updated successfully!"
        )

        return redirect(
            "opportunity_detail",
            id=opportunity.id
        )

    return render(
        request,
        "edit_opportunity.html",
        {
            "opportunity": opportunity
        }
    )


# delete opportunity
@login_required
def delete_opportunity(request, id):

    opportunity = get_object_or_404(Opportunity, id=id)

    # Only the owner can delete
    if opportunity.posted_by != request.user:
        messages.error(
            request,
            "You are not allowed to delete this opportunity."
        )
        return redirect("opportunity_detail", id=opportunity.id)

    if request.method == "POST":

        opportunity.delete()

        messages.success(
            request,
            "Opportunity deleted successfully!"
        )

        return redirect("home")

    return render(
        request,
        "delete_opportunity.html",
        {
            "opportunity": opportunity
        }
    )


# Apply opportunity
@login_required
def apply_opportunity(request, id):

    # Only POST requests can submit an application
    if request.method != "POST":
        return redirect("opportunity_detail", id=id)

    opportunity = get_object_or_404(
        Opportunity,
        id=id
    )

    # Creator cannot apply
    if opportunity.posted_by == request.user:
        messages.error(
            request,
            "You cannot apply to your own opportunity."
        )
        return redirect("opportunity_detail", id=id)

    # Check available seats
    accepted_count = Application.objects.filter(
        opportunity=opportunity,
        status="accepted"
    ).count()

    if accepted_count >= opportunity.students_needed:
        messages.error(
            request,
            "No seats available for this opportunity."
        )
        return redirect("opportunity_detail", id=id)

    # Check if user already has a pending application
    pending_application = Application.objects.filter(
        opportunity=opportunity,
        applicant=request.user,
        status="pending"
    ).exists()

    if pending_application:
        messages.warning(
            request,
            "Your application is still pending."
        )
        return redirect("opportunity_detail", id=id)

    # Check if already accepted
    accepted_application = Application.objects.filter(
        opportunity=opportunity,
        applicant=request.user,
        status="accepted"
    ).exists()

    if accepted_application:
        messages.warning(
            request,
            "You are already accepted for this opportunity."
        )
        return redirect("opportunity_detail", id=id)

    # Create new application
    application = Application.objects.create(
        opportunity=opportunity,
        applicant=request.user
    )

    # Create notification for opportunity creator
    Notification.objects.create(
        user=opportunity.posted_by,
        message=f"{request.user.username} applied to '{opportunity.title}'.",
        opportunity=opportunity,
        application=application
    )

    messages.success(
        request,
        "Application submitted successfully!"
    )

    return redirect(
        "opportunity_detail",
        id=id
    )

@login_required
def my_opportunities(request):

    opportunities = Opportunity.objects.filter(
    posted_by=request.user
    ).order_by("-created_at")

    for opportunity in opportunities:
        opportunity.accepted_count = Application.objects.filter(
            opportunity=opportunity,
            status="accepted"
        ).count()

        opportunity.seats_left = (
            opportunity.students_needed - opportunity.accepted_count
        )

    return render(request, "my_opportunities.html", {
        "opportunities": opportunities
    })

# My_Appliactions :-
@login_required
def my_applications(request):

    applications = Application.objects.filter(
        applicant=request.user
    ).select_related(
        "opportunity"
    ).order_by("-applied_at")

    for application in applications:

        if application.status == "accepted":

            application.conversation = Conversation.objects.filter(
                opportunity=application.opportunity,
                applicant=request.user,
                status="active"
            ).order_by("-created_at").first()

    return render(
        request,
        "my_applications.html",
        {
            "applications": applications
        }
    )

# creator ke liye view applicant :-
@login_required
def opportunity_applications(request, id):

    opportunity = get_object_or_404(
        Opportunity,
        id=id
    )

    # Only creator can view applications
    if opportunity.posted_by != request.user:
        return redirect("home")

    applications = Application.objects.filter(
        opportunity=opportunity
    ).select_related(
        "applicant",
        "applicant__profile"
    ).order_by("-applied_at")

    # Get only active conversation for accepted applicants
    for application in applications:

        if application.status == "accepted":

            application.conversation = Conversation.objects.filter(
                opportunity=opportunity,
                applicant=application.applicant,
                status="active"
            ).first()

    accepted_count = applications.filter(
        status="accepted"
    ).count()

    available_seats = (
        opportunity.students_needed - accepted_count
    )

    return render(request, "opportunity_applications.html", {
        "opportunity": opportunity,
        "applications": applications,
        "accepted_count": accepted_count,
        "available_seats": available_seats,
    })


# Accept application :-
@login_required
def accept_application(request, id):

    # Only POST requests can accept an application
    if request.method != "POST":
        return redirect("home")

    application = get_object_or_404(
        Application,
        id=id
    )

    opportunity = application.opportunity

    # Only opportunity creator can accept an application
    if opportunity.posted_by != request.user:
        messages.error(
            request,
            "You are not allowed to manage this application."
        )
        return redirect("home")

    accepted_count = Application.objects.filter(
        opportunity=opportunity,
        status="accepted"
    ).count()

    # Application must still be pending
    if application.status != "pending":

        messages.error(
            request,
            "This application has already been processed."
        )

    # Check available seats
    elif accepted_count < opportunity.students_needed:

        # Accept application
        application.status = "accepted"
        application.save()

        # Create a new active conversation
        conversation, created = Conversation.objects.get_or_create(
            opportunity=opportunity,
            creator=opportunity.posted_by,
            applicant=application.applicant,
            status="active"
        )

        # Notify applicant
        Notification.objects.create(
            user=application.applicant,
            message=f"Your application for '{opportunity.title}' was accepted.",
            opportunity=opportunity,
            application=application
        )

        # A member has joined again
        if opportunity.member_left:

            opportunity.member_left = False

            opportunity.save(
                update_fields=["member_left"]
            )

        messages.success(
            request,
            "Application accepted successfully!"
        )

    else:

        messages.error(
            request,
            "No seats available for this opportunity."
        )

    return redirect(
        "opportunity_applications",
        id=opportunity.id
    )

@login_required
def leave_team(request, id):

    application = get_object_or_404(
        Application,
        id=id,
        applicant=request.user
    )

    # Only POST requests can leave a team
    if request.method != "POST":
        return redirect("my_applications")

    # Only accepted members can leave
    if application.status != "accepted":
        messages.error(
            request,
            "You cannot leave this team."
        )
        return redirect("my_applications")

    opportunity = application.opportunity

    # Mark the member as left
    application.status = "left"
    application.save()

    # End the conversation
    conversation = Conversation.objects.filter(
        opportunity=opportunity,
        applicant=request.user,
        status="active"
    ).first()

    if conversation:
        conversation.status = "ended"
        conversation.save()

    # Mark that a member has left
    opportunity.member_left = True
    opportunity.save(
        update_fields=["member_left"]
    )

    # Notify the opportunity creator
    Notification.objects.create(
        user=opportunity.posted_by,
        message=(
            f"{request.user.username} has left your team for "
            f"'{opportunity.title}'."
        ),
        opportunity=opportunity,
        application=application
    )

    messages.success(
        request,
        f"You have left '{opportunity.title}'."
    )

    return redirect("my_applications")

@login_required
def remove_member(request, id):

    application = get_object_or_404(
        Application,
        id=id
    )

    opportunity = application.opportunity

    # Only the opportunity creator can remove a member
    if opportunity.posted_by != request.user:
        messages.error(
            request,
            "You are not allowed to remove this member."
        )
        return redirect("home")

    # Only POST requests can remove a member
    if request.method != "POST":
        return redirect(
            "opportunity_applications",
            id=opportunity.id
        )

    # Only accepted members can be removed
    if application.status != "accepted":
        messages.error(
            request,
            "Only accepted members can be removed."
        )
        return redirect(
            "opportunity_applications",
            id=opportunity.id
        )

    # Mark the member as left
    application.status = "left"
    application.save()

    # End the conversation
    conversation = Conversation.objects.filter(
        opportunity=opportunity,
        applicant=application.applicant,
        status="active"
    ).first()

    if conversation:
        conversation.status = "ended"
        conversation.save()

    # Mark that a member has been removed
    opportunity.member_left = True
    opportunity.save(
        update_fields=["member_left"]
    )

    # Notify the removed member
    Notification.objects.create(
        user=application.applicant,
        message=(
            f"You have been removed from the team for "
            f"'{opportunity.title}'."
        ),
        opportunity=opportunity,
        application=application
    )

    messages.success(
        request,
        f"{application.applicant.username} has been removed from your team."
    )

    return redirect(
        "opportunity_applications",
        id=opportunity.id
    )
# Reject application :- 
@login_required
def reject_application(request, id):

    if request.method != "POST":
        return redirect("home")

    application = get_object_or_404(
        Application,
        id=id
    )

    opportunity = application.opportunity

    # Only the opportunity creator can reject applications
    if opportunity.posted_by != request.user:
        messages.error(
            request,
            "You are not allowed to manage this application."
        )
        return redirect("home")

    # Only pending applications can be rejected
    if application.status != "pending":
        messages.error(
            request,
            "This application has already been processed."
        )
        return redirect(
            "opportunity_applications",
            id=opportunity.id
        )

    application.status = "rejected"
    application.save()

    Notification.objects.create(
        user=application.applicant,
        message=f"Your application for '{opportunity.title}' was rejected.",
        opportunity=opportunity,
        application=application
    )

    messages.success(
        request,
        "Application rejected successfully."
    )

    return redirect(
        "opportunity_applications",
        id=opportunity.id
    )

# Notifications
@login_required
def notifications(request):

    notifications = Notification.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(request, "notifications.html", {
        "notifications": notifications
    })


# Mark all notifications as read
@login_required
def mark_all_notifications_read(request):

    if request.method != "POST":
        return redirect("notifications")

    Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True)

    return redirect("notifications")

@login_required
def open_notification(request, id):

    notification = get_object_or_404(
        Notification,
        id=id,
        user=request.user
    )

    # Mark notification as read
    notification.is_read = True
    notification.save()

    if notification.opportunity:

        # Notification received by opportunity creator
        if notification.user == notification.opportunity.posted_by:
            return redirect(
                "opportunity_applications",
                id=notification.opportunity.id
            )

        # Urgent member notification
        if notification.notification_type == "urgent":
            return redirect(
                "opportunity_detail",
                id=notification.opportunity.id
            )

    # Application-related notification
    if notification.application:

        if notification.application.status == "accepted":
            return redirect(
                "application_accepted",
                id=notification.opportunity.id
            )

        elif notification.application.status == "rejected":
            return redirect(
                "application_rejected",
                id=notification.opportunity.id
            )

        elif notification.application.status == "left":
            return redirect(
                "opportunity_detail",
                id=notification.opportunity.id
            )

        return redirect("notifications")

    return redirect("notifications")

@login_required
def profile(request):
    profile = Profile.objects.get(user=request.user)

    return render(request, "profile.html", {
        "profile": profile
    })

@login_required
def edit_profile(request):

    profile = Profile.objects.get(user=request.user)

    if request.method == "POST":

        profile.course = request.POST.get("course")
        profile.year = request.POST.get("year")
        profile.specialization = request.POST.get("specialization")
        profile.skills = request.POST.get("skills")
        profile.bio = request.POST.get("bio")

        profile.save()

        messages.success(
            request,
            "Profile updated successfully!"
        )

        return redirect("home")

    return render(request, "edit_profile.html", {
        "profile": profile
    })

@login_required
def applicant_profile(request, id):

    application = get_object_or_404(
        Application.objects.select_related(
            "applicant",
            "applicant__profile",
            "opportunity"
        ),
        id=id
    )

    # Only opportunity creator can view applicant
    if application.opportunity.posted_by != request.user:
        return redirect("home")

    return render(request, "applicant_profile.html", {
        "application": application
    })

# Application accepted page :-
@login_required
def application_accepted(request, id):

    application = get_object_or_404(
        Application,
        opportunity_id=id,
        applicant=request.user,
        status="accepted"
    )

    return render(
        request,
        "application_accepted.html",
        {
            "opportunity": application.opportunity
        }
    )

@login_required
def application_rejected(request, id):

    application = get_object_or_404(
        Application,
        opportunity_id=id,
        applicant=request.user,
        status="rejected"
    )

    return render(
        request,
        "application_rejected.html",
        {
            "opportunity": application.opportunity
        }
    )

@login_required
def settings(request):
    return render(request, "settings.html")

@login_required
def change_password(request):

    if request.method == "POST":

        old_password = request.POST.get("old_password", "")
        new_password = request.POST.get("new_password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not request.user.check_password(old_password):

            messages.error(
                request,
                "Current password is incorrect."
            )

        elif new_password != confirm_password:

            messages.error(
                request,
                "New passwords do not match."
            )

        elif old_password == new_password:

            messages.error(
                request,
                "New password cannot be the same as your current password."
            )

        else:

            try:
                validate_password(
                    new_password,
                    request.user
                )

            except ValidationError as error:

                for message in error.messages:
                    messages.error(request, message)

            else:

                request.user.set_password(new_password)
                request.user.save()

                update_session_auth_hash(
                    request,
                    request.user
                )

                messages.success(
                    request,
                    "Password changed successfully."
                )

                return redirect("settings")

    return render(
        request,
        "change_password.html"
    )

@login_required
def toggle_notifications(request):

    if request.method != "POST":
        return redirect("settings")

    profile = request.user.profile

    profile.notifications_enabled = not profile.notifications_enabled
    profile.save()

    return redirect("settings")

@login_required
def chat(request, id):

    conversation = get_object_or_404(
        Conversation,
        id=id
    )

    # Check if user belongs to this conversation
    if request.user not in [
        conversation.creator,
        conversation.applicant
    ]:
        messages.error(
            request,
            "You are not allowed to access this chat."
        )
        return redirect("home")

    # Chat must still be active
    if conversation.status == "ended":
        messages.error(
            request,
            "This chat has ended. You cannot send or receive new messages."
        )
        return redirect("home")

    if request.method == "POST":

        content = request.POST.get("content", "").strip()

        if content:

            message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )

            # If request is AJAX, return message as JSON
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":

                return JsonResponse({
                    "id": message.id,
                    "sender": message.sender.username,
                    "content": message.content,
                    "created_at": message.created_at.strftime(
                        "%d %b, %I:%M %p"
                    ),
                    "is_sender": True,
                })

        # Normal request fallback
        return redirect("chat", id=conversation.id)

    # Mark incoming messages as read
    Message.objects.filter(
        conversation=conversation,
        is_read=False
    ).exclude(
        sender=request.user
    ).update(is_read=True)

    messages_list = Message.objects.filter(
        conversation=conversation
    ).order_by("created_at")

    return render(
        request,
        "chat.html",
        {
            "conversation": conversation,
            "chat_messages": messages_list,
        }
    )

@login_required
def urgent_member(request, id):
    # Only POST requests can send urgent notifications
    if request.method != "POST":
        return redirect("home")

    opportunity = get_object_or_404(
        Opportunity,
        id=id
    )

    # Only the opportunity creator can send urgent notifications
    if opportunity.posted_by != request.user:
        messages.error(
            request,
            "You are not allowed to send this notification."
        )
        return redirect("home")

    # Urgent notification is only available when a member has left
    if not opportunity.member_left:
        messages.error(
            request,
            "Urgent notification is only available after a member leaves the team."
        )
        return redirect(
            "opportunity_applications",
            id=opportunity.id
        )

    # Calculate current available seats
    accepted_count = Application.objects.filter(
        opportunity=opportunity,
        status="accepted"
    ).count()

    available_seats = opportunity.students_needed - accepted_count

    # Make sure there is actually a vacancy
    if available_seats <= 0:
        messages.error(
            request,
            "There are no available seats."
        )
        return redirect(
            "opportunity_applications",
            id=opportunity.id
        )

    # Get users who have not already applied
    existing_applicants = Application.objects.filter(
        opportunity=opportunity
    ).values_list(
        "applicant_id",
        flat=True
    )

    eligible_users = User.objects.exclude(
        id=request.user.id
    ).exclude(
        id__in=existing_applicants
    )

    # Check whether there is anyone to notify
    if not eligible_users.exists():
        messages.error(
            request,
            "There are no eligible users to notify."
        )
        return redirect(
            "opportunity_applications",
            id=opportunity.id
        )

    # Send urgent notification to eligible users
    for user in eligible_users:

        Notification.objects.create(
            user=user,
            message=(
                f"🚨 Urgent Requirement: "
                f"'{opportunity.title}' needs "
                f"{available_seats} more member"
                f"{'s' if available_seats != 1 else ''}."
            ),
            opportunity=opportunity,
            notification_type="urgent"
        )

    # Urgent notification has now been used for this vacancy
    opportunity.member_left = False
    opportunity.save(
        update_fields=["member_left"]
    )

    messages.success(
        request,
        "Urgent member notification sent successfully!"
    )

    return redirect(
        "opportunity_applications",
        id=opportunity.id
    )

@login_required
def messages_view(request):

    conversations = Conversation.objects.filter(
        status="active"
    ).filter(
        Q(creator=request.user) |
        Q(applicant=request.user)
    ).select_related(
        "opportunity",
        "creator",
        "applicant"
    ).order_by("-created_at")

    for conversation in conversations:

        # Current user ke opposite user ko identify karo
        if conversation.creator == request.user:
            conversation.other_user = conversation.applicant
        else:
            conversation.other_user = conversation.creator

        # Latest message nikalo
        conversation.last_message = conversation.messages.order_by(
            "-created_at"
        ).first()

        # Current user ke unread messages count karo
        conversation.unread_count = conversation.messages.filter(
            is_read=False
        ).exclude(
            sender=request.user
        ).count()

    return render(
        request,
        "messages.html",
        {
            "conversations": conversations
        }
    )

@login_required
def chat_messages(request, id):

    conversation = get_object_or_404(
        Conversation,
        id=id
    )

    # Check if user belongs to this conversation
    if request.user not in [
        conversation.creator,
        conversation.applicant
    ]:
        return JsonResponse(
            {
                "error": "You are not allowed to access this chat."
            },
            status=403
        )

    # Chat must still be active
    if conversation.status == "ended":
        return JsonResponse(
            {
                "error": "This chat has ended."
            },
            status=403
        )

    # Mark incoming messages as read
    Message.objects.filter(
        conversation=conversation,
        is_read=False
    ).exclude(
        sender=request.user
    ).update(
        is_read=True
    )

    # Get all messages
    messages_list = Message.objects.filter(
        conversation=conversation
    ).order_by("created_at")

    messages_data = []

    for message in messages_list:

        messages_data.append({
            "id": message.id,
            "sender": message.sender.username,
            "content": message.content,
            "created_at": message.created_at.strftime(
                "%d %b, %I:%M %p"
            ),
            "is_sender": message.sender == request.user,
        })

    # Get remaining unread messages from other active conversations
    unread_count = Message.objects.filter(
        conversation__status="active",
        is_read=False
    ).exclude(
        sender=request.user
    ).filter(
        Q(conversation__creator=request.user) |
        Q(conversation__applicant=request.user)
    ).count()

    return JsonResponse({
        "messages": messages_data,
        "unread_count": unread_count,
    })

