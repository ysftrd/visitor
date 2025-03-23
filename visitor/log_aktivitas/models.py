from django.db import models
from user_auth.models import Users

class ActivityLogs(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='activity_logs')
    aktivitas = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.aktivitas} by {self.user.username}"