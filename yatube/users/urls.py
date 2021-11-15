from django.contrib.auth.views import (LoginView, LogoutView,
                                       PasswordChangeDoneView,
                                       PasswordChangeView,
                                       PasswordResetCompleteView,
                                       PasswordResetConfirmView,
                                       PasswordResetDoneView,
                                       PasswordResetView)
from django.urls import path

from . import views

app_name = 'users'

urlpatterns = [
    # Регистрация - после регистрации  - переход на главную страницу
    path('signup/', views.SignUp.as_view(), name='signup'),

    # Выход из учетной записи - пока ни к чему не привязано
    path('logout/', LogoutView.as_view(
        template_name='users/logged_out.html'), name='logout'),

    # Логин - после - переход на главную страницу
    path('login/', LoginView.as_view(
        template_name='users/login.html'), name='login'),

    # Форма изменения пароля залогинившегося юзера. В случае успешный операции
    # переход на форму успешно изменен. Есть переход на главную страницу
    path('password_change/', PasswordChangeView.as_view(
        template_name='users/password_change_form.html', success_url='done'
    ), name='password_change'),
    path('password_change/done', PasswordChangeDoneView.as_view(
        template_name='users/password_change_done.html'
    ), name='password_change_done'),

    # Последовательность: login/(забыли пароль) -> password_reset/ ->
    # password_reset/done -> Открываем sent_emails переходим по ссылке ->
    # reset/<uidb64>/<token>/ -> reset/<uidb64>/<token>/done
    path('password_reset/', PasswordResetView.as_view(
        template_name='users/password_reset_form.html',
        success_url='done'), name='password_reset'),
    path('password_reset/done', PasswordResetDoneView.as_view(
        template_name='users/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(
        template_name='users/password_reset_confirm.html',
        success_url='done'), name='password_reset_confirm'),
    path('reset/<uidb64>/<token>/done', PasswordResetCompleteView.as_view(
        template_name='users/password_reset_complete.html'
    ), name='reset_done'),
]
