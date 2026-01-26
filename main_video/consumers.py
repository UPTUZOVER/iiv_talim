import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Comment, Video, Users

class CommentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.video_id = self.scope['url_route']['kwargs']['video_id']
        self.group_name = f"comments_video_{self.video_id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        comment_text = data.get('comment')
        user = self.scope['user']

        if not user.is_authenticated:
            await self.send(text_data=json.dumps({'error': 'Not authenticated'}))
            return

        comment = await self.create_comment(user, comment_text, self.video_id)

        # Barcha userlarga yuborish
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'comment_message',
                'id': comment.id,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'role': user.role
                },
                'comment': comment.comment,
                'created_at': str(comment.created_at)
            }
        )

    async def comment_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def create_comment(self, user, comment_text, video_id):
        video = Video.objects.get(id=video_id)
        return Comment.objects.create(user=user, video=video, comment=comment_text)
