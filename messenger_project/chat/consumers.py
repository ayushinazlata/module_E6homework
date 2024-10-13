from channels.generic.websocket import AsyncWebsocketConsumer
import json

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Получаем тип чата и имя комнаты
        self.chat_type = self.scope['url_route']['kwargs']['chat_type']
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        
        # Формируем название группы на основе типа чата
        self.room_group_name = f'{self.chat_type}_{self.room_name}'

        # Присоединяемся к группе чата
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()  # Принимаем соединение

    async def disconnect(self, close_code):
        # Отключаемся от группы
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        username = text_data_json['username']

        # Отправляем сообщение в группу чата
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username
            }
        )

    async def chat_message(self, event):
        message = event['message']
        username = event['username']

        # Отправляем сообщение пользователю
        await self.send(text_data=json.dumps({
            'message': message,
            'username': username
        }))
