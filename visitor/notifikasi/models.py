from django.db import models
from user_auth.models import Users

class Notifications(models.Model):
    STATUS_CHOICES = (
        ('unread', 'Unread'),
        ('read', 'Read'),
    )
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='notifications')
    pesan = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unread')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}"