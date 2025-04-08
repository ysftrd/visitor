from django.db import models
from user_auth.models import Users

class ActivityLog(models.Model):
    user = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True, related_name='activity_logs')
    action = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email if self.user else 'Unknown'} - {self.action} at {self.timestamp}"