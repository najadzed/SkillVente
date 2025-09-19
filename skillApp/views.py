from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Swaprequest, Profile, Skill, Review,ChatMessage,Notification
from django.contrib.auth import authenticate, login as auth_login,logout as auth_logout
from django.db.models import Avg
from django.http import JsonResponse
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

def home_page(request):
    return render(request, 'home.html')

def loguot_view(request):
    auth_logout(request)
    messages.info(request,"you have been Logged out!")
    return redirect("login")

@login_required
def dashboard(request):
    profile = request.user.profile
    skills = profile.skills.all()

    # ✅ Check if profile image is default
    is_default_profile_image = False
    if profile.profile_image and profile.profile_image.name.endswith("default.png"):
        is_default_profile_image = True

    # ✅ Notifications
    notifications = (
        request.user.notifications.all().order_by("-created_at")
        if hasattr(request.user, "notifications")
        else []
    )

    # ✅ Incoming Swap Requests
    incoming_requests = (
        request.user.swap_requests_received.select_related("from_user", "to_user")
        .prefetch_related("reviews")
        .all()
        .order_by("-created")
        if hasattr(request.user, "swap_requests_received")
        else []
    )

    # ✅ Reviews
    reviews_received = (
        Review.objects.filter(swap_request__to_user=request.user)
        .select_related("swap_request", "reviewer")
        .order_by("-created_at")
    )
    reviews_given = (
        request.user.reviews_given.select_related("swap_request", "reviewer")
        .all()
        .order_by("-created_at")
        if hasattr(request.user, "reviews_given")
        else []
    )

    # ✅ Chats
    chats = (
        request.user.chats.select_related("sender", "receiver").all().order_by("-timestamp")
        if hasattr(request.user, "chats")
        else []
    )

    # ✅ Top Reviewed Profiles
    top_reviewed = (
        User.objects.annotate(avg_rating=Avg("swap_requests_received__reviews__rating"))
        .filter(avg_rating__isnull=False)
        .order_by("-avg_rating")[:6]
    )

    # ✅ Recent Activity
    recent_activity = []

    context = {
        "profile": profile,
        "skills": skills,
        "notifications": notifications,
        "incoming_requests": incoming_requests,
        "reviews_received": reviews_received,
        "reviews_given": reviews_given,
        "chats": chats,
        "top_reviewed": top_reviewed,
        "recent_activity": recent_activity,
        "is_default_profile_image": is_default_profile_image,  # 👈 added
    }

    return render(request, "dashboard.html", context)

# Password Reset Request View
class CustomPasswordResetView(auth_views.PasswordResetView):
    template_name = "password_reset.html"
    email_template_name = "password_reset_email.html"
    subject_template_name = "password_reset_subject.txt"
    success_url = reverse_lazy("password_reset_done")

# Password Reset Done View
class CustomPasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = "password_reset_done.html"

# Password Reset Confirm View
class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")

# Password Reset Complete View
class CustomPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = "password_reset_complete.html"


def reg_page(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")  # ✅ match register.html
        password2 = request.POST.get("password2")

        # Validation
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken!")
            return redirect("register")

        if password1 != password2:
            messages.error(request, "Passwords do not match!")
            return redirect("register")

        if len(password1) < 6:
            messages.error(request, "Password must be at least 6 characters long!")
            return redirect("register")

        # Create user
        user = User.objects.create_user(username=username, email=email, password=password1)
        Profile.objects.create(user=user)

        messages.success(request, "Account created successfully! You can now login.")
        return redirect("login")

    return render(request, 'register.html')

def login_page(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            auth_login(request, user)
            return redirect("dashboard")  # ✅ fixed
        else:
            messages.error(request, "Invalid username or password")
    return render(request, "login.html")

@login_required
def profile(request, username):
    user = get_object_or_404(User, username=username)
    profile = user.profile
    return render(request, "profile.html", {
        "profile": profile,
        "user_obj": user   # pass user explicitly
    })

@login_required
def profile_view(request, username):
    user_obj = get_object_or_404(User, username=username)
    profile = user_obj.profile
    skills = profile.skills.all()
    reviews = Review.objects.filter(swap_request__to_user=user_obj)

    context = {
        "user_obj": user_obj,
        "profile": profile,
        "skills": skills,
        "reviews": reviews,
    }
    return render(request, "profile_view.html", context)

@login_required
def edit_profile(request):
    profile = request.user.profile
    if request.method == 'POST':
        profile.full_name = request.POST.get("full_name")
        profile.bio = request.POST.get("bio")
        profile.location = request.POST.get("location")
        profile.looking_to_learn = request.POST.get("looking_to_learn")

        # ✅ Handle profile photo
        if "profile_image" in request.FILES:
            profile.profile_image = request.FILES["profile_image"]

        profile.save()

        messages.success(request, "Profile updated successfully!")
        return redirect("profile", username=request.user.username)

    return render(request, "edit_profile.html", {"profile": profile})


@login_required
def add_skill(request):
    if request.method == 'POST':
        name = request.POST.get("name")
        category = request.POST.get("category")
        can_teach = bool(request.POST.get("can_teach"))
        want_to_learn = bool(request.POST.get("want_to_learn"))

        Skill.objects.create(
            profile=request.user.profile,
            name=name,
            category=category,
            can_teach=can_teach,
            want_to_learn=want_to_learn,
        )
        messages.success(request, "Skill added successfully!")
        return redirect("my_skills")  # ✅ back to skills page

    return render(request, "add_skill.html")
@login_required
def delete_skill(request, skill_id):
    skill = get_object_or_404(Skill, id=skill_id, profile=request.user.profile)
    skill_name = skill.name
    skill.delete()
    messages.success(request, f"Skill '{skill_name}' deleted successfully.")
    return redirect("my_skills")

@login_required
def find_skills(request):
    query = request.GET.get("q", "")
    skills = Skill.objects.exclude(profile=request.user.profile)

    if query:
        skills = skills.filter(name__icontains=query)

    return render(request, "find_skills.html", {"skills": skills, "query": query})
@login_required
def my_skills(request):
    skills = request.user.profile.skills.all()
    return render(request, "my_skills.html", {"skills": skills})

@login_required
def send_swap_request(request, skill_id):
    requested_skill = get_object_or_404(Skill, id=skill_id)
    offered_skill = Skill.objects.filter(profile=request.user.profile, can_teach=True).first()

    if not offered_skill:
        messages.error(request, "You must add at least one skill you can teach before sending a swap request.")
        return redirect("my_skills")

    if requested_skill.profile.user == request.user:
        messages.error(request, "You cannot send a swap request to yourself.")
        return redirect("find_skills")

    # ✅ Prevent multiple duplicates
    existing = Swaprequest.objects.filter(
        from_user=request.user,
        to_user=requested_skill.profile.user,
        offered_skill=offered_skill,
        requested_skill=requested_skill,
    ).first()

    if existing:
        messages.info(request, "You already sent a request for this skill.")
    else:
        Swaprequest.objects.create(
            from_user=request.user,
            to_user=requested_skill.profile.user,
            offered_skill=offered_skill,
            requested_skill=requested_skill,
            status="pending"
        )
        messages.success(request, f"Swap request sent to {requested_skill.profile.user.username}!")

    return redirect("swap_requests")


@login_required
def handle_swap_request(request, request_id, action):
    swap_request = get_object_or_404(Swaprequest, id=request_id)

    if action == "accept":
        swap_request.status = "accepted"
        messages.success(request, "Swap request accepted!")
    elif action == "decline":
        swap_request.status = "declined"
        messages.info(request, "Swap request declined.")

    swap_request.save()
    return redirect("swap_requests")

@login_required
def swap_requests(request):
    incoming = Swaprequest.objects.filter(to_user=request.user)
    outgoing = Swaprequest.objects.filter(from_user=request.user)

    return render(request, "swap_requests.html", {
        "incoming_requests": incoming,
        "outgoing_requests": outgoing,
    })

@login_required
def chat_view(request, request_id):
    swap_request = get_object_or_404(Swaprequest, id=request_id)

    # security check: only participants can see chat
    if request.user not in [swap_request.from_user, swap_request.to_user]:
        return redirect("swap_requests")

    if request.method == "POST":
        msg = request.POST.get("message")
        if msg.strip():
            # Save the chat message
            ChatMessage.objects.create(
                swap_request=swap_request,
                sender=request.user,
                message=msg
            )

            # Determine the recipient
            recipient = swap_request.to_user if request.user == swap_request.from_user else swap_request.from_user

            # Create notification for the recipient
            Notification.objects.create(
                user=recipient,
                message=f"💬 New message from {request.user.username}",
                link=f"/chat/{swap_request.id}/"
            )

        return redirect("chat", request_id=request_id)

    messages = ChatMessage.objects.filter(swap_request=swap_request).order_by("timestamp")
    return render(request, "chat.html", {
        "swap_request": swap_request,
        "messages": messages
    })


@login_required
def delete_swap_request(request, request_id):
    swap_request = get_object_or_404(Swaprequest, id=request_id)

    # Only allow owner (from_user) or recipient (to_user) to delete
    if request.user not in [swap_request.from_user, swap_request.to_user]:
        return redirect("swap_requests")

    swap_request.delete()
    messages.success(request, "Swap request deleted successfully.")
    return redirect("swap_requests")

@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")

    # mark all as read when opened
    notifications.update(is_read=True)

    return render(request, "notifications.html", {"notifications": notifications})

@login_required
def mark_notifications_read(request):
    if request.method == "POST":
        # mark all as read for the logged-in user
        if hasattr(request.user, "notifications"):
            request.user.notifications.update(is_read=True)
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

@login_required
def add_review(request, request_id):
    swap_request = get_object_or_404(Swaprequest, id=request_id)

    # prevent duplicate reviews
    if Review.objects.filter(swap_request=swap_request, reviewer=request.user).exists():
        messages.warning(request, "You have already reviewed this swap.")
        return redirect("profile", username=swap_request.to_user.username)

    if request.method == "POST":
        rating = int(request.POST.get("rating"))
        comment = request.POST.get("comment")

        Review.objects.create(
            swap_request=swap_request,
            reviewer=request.user,
            rating=rating,
            comment=comment,
        )
        messages.success(request, "Review submitted!")
        return redirect("profile", username=swap_request.to_user.username)

    return render(request, "add_review.html", {"swap_request": swap_request})


@login_required
def reviews_page(request):
    reviews = Review.objects.filter(swap_request__to_user=request.user)
    return render(request, "reviews.html", {"reviews": reviews})
