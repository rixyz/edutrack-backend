from django.db import models

from users.models import User

# Create your models here.


class Messages(models.Model):
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages"
    )
    receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_messages"
    )
    content = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def save_message(cls, sender, receiver, content):
        return cls.objects.create(sender=sender, receiver=receiver, content=content)

    def __str__(self):
        return f"({self.sender.id} -> {self.receiver.id}) {self.content}"
