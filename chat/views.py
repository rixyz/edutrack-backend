from django.db.models import Max, Q, Subquery
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from chat.models import Messages
from chat.serializers import ChatListSerializer, MessageSerializer
from users.models import User


class ChatListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

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
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, receiver_id):
        receiver = get_object_or_404(User, id=receiver_id)

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

    # def post(self, request, receiver_id):
    #     receiver = get_object_or_404(User, id=receiver_id)

    #     serializer = MessageSerializer(data=request.data)

    #     if serializer.is_valid():
    #         new_message = Messages.objects.create(
    #             sender=request.user,
    #             receiver=receiver,
    #             content=serializer.validated_data["content"],
    #         )

    #         response_serializer = MessageSerializer(new_message)
    #         return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
