from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, default="Not specified")
    looking_to_learn = models.CharField(max_length=200, blank=True)  # new
    profile_image = models.ImageField(upload_to='profile_pics/', default='default.png')
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

    
class Skill(models.Model):
    profile = models.ForeignKey(Profile,on_delete=models.CASCADE,related_name="skills")
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100,blank=True)
    can_teach = models.BooleanField(default=False)
    want_to_learn = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.profile.user.username})"

class Swaprequest(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="swap_requests_sent")
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="swap_requests_received")
    offered_skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="offered_in")
    requested_skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="requested_in")

    status = models.CharField(
        max_length=20,
        choices=[("pending", "pending"), ("accepted", "accepted"), ("declined", "declined")],
        default="pending"
    )
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.from_user.username} → {self.to_user.username} ({self.status})"

class ChatMessage(models.Model):
    swap_request = models.ForeignKey("Swaprequest", on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.sender.username}: {self.message[:30]}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Determine the receiver
        if self.sender == self.swap_request.from_user:
            receiver = self.swap_request.to_user
        else:
            receiver = self.swap_request.from_user

        # Create a notification for the receiver
        Notification.objects.create(
            user=receiver,
            message=f"New message from {self.sender.username}",
            link=f"/chat/{self.swap_request.id}/"
        )

class Notification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications"  # 👈 important
    )
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.message}"

class Review(models.Model):
    swap_request = models.ForeignKey(Swaprequest, on_delete=models.CASCADE, related_name="reviews")
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews_given")
    rating = models.IntegerField(default=0)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.reviewer.username} - {self.rating}/5"
