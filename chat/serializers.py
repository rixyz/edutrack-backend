from rest_framework import serializers

from chat.models import Messages
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "profile_picture"]


class ChatListSerializer(serializers.Serializer):
    user = UserSerializer()
    last_message = serializers.CharField()
    last_message_time = serializers.DateTimeField()


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Messages
        fields = ["id", "sender", "receiver", "content", "created_at"]
