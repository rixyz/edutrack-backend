from django.db.models import Max, Q, Subquery
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from chat.models import Messages
from chat.serializers import ChatListSerializer, MessageSerializer
from EduTrack.permissions import CheckPermission
from EduTrack.utils import get_or_not_found
from users.models import User


class ChatListAPIView(APIView):
    permission_classes = [CheckPermission]

    def get(self, request):
        user = request.user
        latest_messages = (
            Messages.objects.filter(Q(sender=user) | Q(receiver=user))
            .values("sender", "receiver")
            .annotate(last_message=Max("id"))
        )
        chats = (
            Messages.objects.filter(
                id__in=Subquery(latest_messages.values("last_message"))
            )
            .select_related("sender", "receiver")
            .order_by("-created_at")
        )

        chat_details = []
        processed_users = set()

        for message in chats:
            other_user = (
                message.sender if message.receiver == user else message.receiver
            )
            if other_user.id in processed_users:
                continue
            chat_details.append(
                {
                    "user": other_user,
                    "last_message": message.content,
                    "last_message_time": message.created_at,
                }
            )
            processed_users.add(other_user.id)

        serializer = ChatListSerializer(data=chat_details, many=True)
        serializer.is_valid()
        return Response(
            {
                "message": "Messages retrieved successfully",
                "data": serializer.data,
                "status": "data_retrieved",
            },
            status=status.HTTP_200_OK,
        )


class ChatRoomAPIView(APIView):
    permission_classes = [CheckPermission]

    def get(self, request, receiver_id):
        receiver = get_or_not_found(User.objects.all(), pk=receiver_id)

        messages = Messages.objects.filter(
            (Q(sender=request.user) & Q(receiver=receiver))
            | (Q(sender=receiver) & Q(receiver=request.user))
        ).order_by("created_at")

        serializer = MessageSerializer(messages, many=True)
        return Response(
            {
                "message": "Messages retrieved successfully",
                "data": serializer.data,
                "status": "data_retrieved",
            },
            status=status.HTTP_200_OK,
        )
