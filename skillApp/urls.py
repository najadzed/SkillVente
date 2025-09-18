from django.urls import path
from . import views
from .views import (
    CustomPasswordResetView,
    CustomPasswordResetDoneView,
    CustomPasswordResetConfirmView,
    CustomPasswordResetCompleteView,
)
urlpatterns = [
    # Home & Auth
    path("", views.home_page, name="home"),
    path("login/", views.login_page, name="login"),
    path("register/", views.reg_page, name="register"),
    path("logout/", views.loguot_view, name="logout"),

    # Dashboard & Profile
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("profile/<str:username>/", views.profile, name="profile"),
    path("profile/<str:username>/view/", views.profile_view, name="profile_view"),
    
    # Skills
    path("skills/", views.my_skills, name="my_skills"),
    path("skills/add/", views.add_skill, name="add_skill"),
    path("find-skills/", views.find_skills, name="find_skills"),
    path("skills/<int:skill_id>/delete/", views.delete_skill, name="delete_skill"),


    # Swap Requests
    path("swap-requests/", views.swap_requests, name="swap_requests"),
    path("swap-requests/send/<int:skill_id>/", views.send_swap_request, name="send_swap_request"),
    path("swap-requests/<int:request_id>/<str:action>/", views.handle_swap_request, name="handle_swap_request"),
    path("swap-requests/delete/<int:request_id>/", views.delete_swap_request, name="delete_swap_request"),


    # Reviews
    path("reviews/", views.reviews_page, name="reviews"),
    path("reviews/add/<int:request_id>/", views.add_review, name="add_review"),
    path("chat/<int:request_id>/", views.chat_view, name="chat"),
    path("notifications/", views.notifications_view, name="notifications"),
    path("notifications/mark-read/", views.mark_notifications_read, name="mark_notifications_read"),
    
    #password reset
    path("password_reset/", CustomPasswordResetView.as_view(), name="password_reset"),
    path("password_reset/done/", CustomPasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", CustomPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", CustomPasswordResetCompleteView.as_view(), name="password_reset_complete"),



]
