from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, Chat


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    avatar = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'avatar']

    def save(self, commit=True):
        user = super().save(commit)
        # Создаем или обновляем профиль пользователя
        profile, created = UserProfile.objects.get_or_create(user=user)
        # Проверяем наличие аватара
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            profile.avatar = avatar
        profile.save()
        
        return user



class ProfileForm(forms.ModelForm):
    username = forms.CharField(max_length=150)

    class Meta:
        model = UserProfile
        fields = ['username', 'avatar']  # Убедитесь, что здесь есть поле для аватара

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ProfileForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['username'].initial = user.username  # Установка текущего име


class ChatForm(forms.ModelForm):
    participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),  # Получаем всех пользователей
        widget=forms.CheckboxSelectMultiple,  # Или используйте SelectMultiple для выпадающего списка
        required=True
    )

    class Meta:
        model = Chat
        fields = ['name', 'participants']  # Указываем только необходимые поля
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }