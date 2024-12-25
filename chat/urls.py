from django.urls import path

from chat.views import ChatListAPIView, ChatRoomAPIView

urlpatterns = [
    path("chat/", ChatListAPIView.as_view(), name="chat_list"),
    path("chat/<int:receiver_id>/", ChatRoomAPIView.as_view(), name="chat_room"),
]
