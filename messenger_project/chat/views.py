from rest_framework import viewsets
from .models import UserProfile, Chat, Message
from .serializers import ChatSerializer, MessageSerializer
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import ProfileForm, UserRegistrationForm, ChatForm
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
import logging


# Класс для обработки входа в систему
class CustomLoginView(LoginView):
    template_name = 'login.html'

    def get_success_url(self):
        return reverse('default')
    

# Страница регистрации
def signup_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)  # Добавьте request.FILES для обработки файлов
        if form.is_valid():
            form.save()
            return redirect('login')  # Перенаправьте после успешной регистрации
    else:
        form = UserRegistrationForm()
    return render(request, 'signup.html', {'form': form})


# Страница выхода из системы
def logout_view(request):
    logout(request)
    return redirect('login')


# Cраница редактирования профиля
logger = logging.getLogger(__name__)

# views.py
@login_required
def profile_view(request):
    try:
        profile, created = UserProfile.objects.get_or_create(user=request.user)

        if request.method == 'POST':
            form = ProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
            if form.is_valid():
                # Сохраняем изменения в профиле
                form.save()
                # Обновляем имя пользователя
                request.user.username = form.cleaned_data['username']
                request.user.save()
                return redirect('profile')  # перенаправление обратно на страницу профиля
        else:
            form = ProfileForm(instance=profile, user=request.user)

        return render(request, 'simple_profile.html', {'form': form, 'profile': profile})

    except Exception as e:
        logger.error(f"Error loading profile: {e}")
        return render(request, 'simple_profile.html', {'form': None, 'error': str(e)})

    


# Страница создания нового чата
def create_chat_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        participants = request.POST.getlist('participants')

        # Добавляем текущего пользователя к участникам
        participants.append(request.user.id)  # Добавляем создателя чата

        # Определяем, групповой это чат или приватный
        if len(participants) >= 3:
            chat = Chat.objects.create(name=name, is_group=True)
            chat.participants.add(*participants)
            return redirect('chat_room', chat_id=chat.id)  # Перенаправление на чат для группового чата
        else:
            chat = Chat.objects.create(name=name, is_group=False)
            chat.participants.add(*participants)
            return redirect('private_chat', user_id=participants[1])  # Перенаправление на личный чат

    # Получаем всех пользователей, кроме текущего
    users = User.objects.exclude(id=request.user.id)
    return render(request, 'create_chat.html', {'users': users})


# Страница редактирования чата
def edit_chat_view(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)  # Получаем чат по ID
    if request.method == 'POST':
        form = ChatForm(request.POST, instance=chat)  # Заполняем форму текущими данными чата
        if form.is_valid():
            form.save()  # Сохраняем изменения
            return redirect('chat_room', chat_id=chat.id)  # Перенаправление на страницу чата
    else:
        form = ChatForm(instance=chat)  # Создаем форму с текущими данными

    return render(request, 'edit_chat.html', {'form': form, 'chat': chat})  # Возвращаем шаблон редактирования


# Страница удаления чата
def delete_chat_view(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    
    # Проверка, что пользователь участвует в чате
    if request.user in chat.participants.all():
        chat.delete()
        return redirect('default')  # Перенаправляем на главную страницу или куда нужно
    else:
        # Обработать случай, если пользователь не может удалить чат
        return render(request, 'error.html', {'message': 'Вы не можете удалить этот чат.'})


# Главная страница (список чатов)
def default_view(request):
    if request.user.is_authenticated:
        user_chats = Chat.objects.filter(participants=request.user)

        # Получаем фильтр из GET параметров
        chat_filter = request.GET.get('filter')

        # Если есть фильтр, применяем его
        if chat_filter == 'private':
            user_chats = user_chats.filter(is_group=False)
        elif chat_filter == 'group':
            user_chats = user_chats.filter(is_group=True)

        # Логика для замены имени чата на "чат с {пользователь}"
        chats_with_names = []
        for chat in user_chats:
            if not chat.is_group and chat.participants.count() == 2:
                # Находим другого участника чата
                other_user = chat.participants.exclude(id=request.user.id).first()
                chat.display_name = f"Chat with {other_user.username}" if other_user else chat.name
            else:
                chat.display_name = chat.name  # Оставляем стандартное имя для групповых чатов
            chats_with_names.append(chat)

        # Пагинация
        paginator = Paginator(chats_with_names, 10)  # 10 чатов на страницу
        page_number = request.GET.get('page')  # Получаем номер страницы из параметров запроса
        page_obj = paginator.get_page(page_number)  # Получаем объект страницы

        return render(request, 'default.html', {'page_obj': page_obj})
    else:
        return render(request, 'default.html', {'message': 'Please log in to see your chats.'})
    

# Страница группового чата по ID
def chat_room_view(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)  # Получаем чат по id
    room_name = chat.name  # Имя комнаты - название чата
    participants_count = chat.participants.count()  # Количество участников

    return render(request, 'chat_room.html', {
        'chat': chat,
        'room_name': room_name,
        'participants_count': participants_count  # Передаем количество участников
    })


# Страница приватного чата с пользователем по ID
@login_required
def private_chat_view(request, user_id):
    # Получаем текущего пользователя
    current_user = request.user

    # Находим другого пользователя
    other_user = get_object_or_404(User, id=user_id)

    # Пытаемся получить чат между текущим пользователем и другим пользователем
    chat = Chat.objects.filter(participants=current_user).filter(participants=other_user)

    # Если чата не существует, можно создать его (если нужно)
    if chat.exists():
        chat = chat.first()  # Получаем первый чат
    else:
        # Если чата не существует, создаем его
        chat = Chat.objects.create(name=f"Chat with {other_user.username}", is_group=False)
        chat.participants.add(current_user, other_user)

    # Здесь вы можете добавить логику для отображения чата
    return render(request, 'privat_chat.html', {'chat': chat, 'other_user': other_user})



# Функция для отображения всех пользователей
def all_users_view(request):
    users_list = User.objects.exclude(id=request.user.id)  # Исключаем текущего пользователя
    paginator = Paginator(users_list, 10)  # Показываем по 10 пользователей на странице
    page_number = request.GET.get('page')
    users = paginator.get_page(page_number)

    return render(request, 'all_users.html', {'users': users})


# ViewSet для API чатов
class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer


# ViewSet для API сообщений
class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def get_queryset(self):
        chat_id = self.request.query_params.get('chat', None)
        if chat_id is not None:
            return self.queryset.filter(chat_id=chat_id)
        return self.queryset

