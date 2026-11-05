from django.urls import path
from home import views
from django.contrib.auth import views as auth_views
urlpatterns = [
    path('register/',views.register_user,name= "register"),
    path("login/", views.login_user, name="login"),
    path(
    "password-reset/",
    auth_views.PasswordResetView.as_view(
        template_name="password_reset.html"
    ),
    name="password_reset"
    ),

    path(
    "password-reset/done/",
    auth_views.PasswordResetDoneView.as_view(
        template_name="password_reset_done.html"
    ),
    name="password_reset_done"
    ),

    path(
    "password-reset-confirm/<uidb64>/<token>/",
    auth_views.PasswordResetConfirmView.as_view(
        template_name="password_reset_confirm.html"
    ),
    name="password_reset_confirm"
    ),

    path(
    "password-reset-complete/",
    auth_views.PasswordResetCompleteView.as_view(
        template_name="password_reset_complete.html"
    ),
    name="password_reset_complete"
    ),

    path("logout/", views.logout_user, name="logout"),
    path("",views.home,name="home"),
    path("create-opportunity/", views.create_opportunity, name="create_opportunity"),
    path("opportunity/<int:id>/", views.opportunity_detail, name="opportunity_detail"),
    path(
    "opportunity/<int:id>/edit/",
    views.edit_opportunity,
    name="edit_opportunity"
    ),

    path(
    "opportunity/<int:id>/delete/",
    views.delete_opportunity,
    name="delete_opportunity"
    ),
    path(
    "opportunity/<int:id>/apply/",
    views.apply_opportunity,
    name="apply_opportunity"
    ),
    path(
    "my-applications/",
    views.my_applications,
    name="my_applications"
    ),
    path(
    "opportunity/<int:id>/applications/",
    views.opportunity_applications,
    name="opportunity_applications"
    ),
    path(
    "application/<int:id>/accept/",
    views.accept_application,
    name="accept_application"
    ),
    path(
    "application/<int:id>/reject/",
    views.reject_application,
    name="reject_application"
    ),
    
    path(
    "my-opportunities/",
    views.my_opportunities,
    name="my_opportunities"
    ),
    path(
    "verify-otp/",
    views.verify_otp,
    name="verify_otp"
    ),
    path(
    "notifications/",
    views.notifications,
    name="notifications"
    ),

path(
    "notifications/read-all/",
    views.mark_all_notifications_read,
    name="mark_all_notifications_read"
    ),

    path(
    "notifications/<int:id>/",
    views.open_notification,
    name="open_notification"
    ),
    path("profile/", views.profile, name="profile"),

    path(
    "profile/edit/",
    views.edit_profile,
    name="edit_profile"
    ),

    path(
    "applicant/<int:id>/",
    views.applicant_profile,
    name="applicant_profile"
    ),
    path(
    "application-accepted/<int:id>/",
    views.application_accepted,
    name="application_accepted"
    ),
    path(
    "application-rejected/<int:id>/",
    views.application_rejected,
    name="application_rejected"
    ),
    path(
    "leave-team/<int:id>/",
    views.leave_team,
    name="leave_team"
    ),
    path(
    "remove-member/<int:id>/",
    views.remove_member,
    name="remove_member"
    ),
    path(
    "urgent-member/<int:id>/",
    views.urgent_member,
    name="urgent_member"
    ),
    path(
    "settings/",
    views.settings,
    name="settings"
    ),
    path(
    "change-password/",
    views.change_password,
    name="change_password"
    ),
    path(
    "toggle-notifications/",
    views.toggle_notifications,
    name="toggle_notifications"
    ),
    path(
    "chat/<int:id>/",
    views.chat,
    name="chat"
    ),
    path("messages/", views.messages_view, name="messages"),
    path(
    "chat-messages/<int:id>/",
    views.chat_messages,
    name="chat_messages"
    ),
]


