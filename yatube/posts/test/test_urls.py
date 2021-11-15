from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовая группа',
            author=cls.author,
            group=cls.group
        )

    def setUp(self):
        # Авторизация автора
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)
        # Создаем пользователя и авторизируем пользователя
        self.user = User.objects.create_user(username='auth1')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_urls_uses_correct_template(self):
        # Шаблоны по адресам доступные всем
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': f'/group/{PostURLTests.post.group.slug}/',
            'posts/profile.html': f'/profile/{PostURLTests.post.author}/',
            'posts/post_detail.html': f'/posts/{PostURLTests.post.pk}/',
        }
        for template, adress in templates_url_names.items():
            with self.subTest(adress=adress):
                # Шаблонами пользуется гость
                response = self.client.get(adress)
                self.assertTemplateUsed(response, template)
                cache.clear()
                # Шаблонами пользуется юзер
                response2 = self.authorized_client.get(adress)
                self.assertTemplateUsed(response2, template)
                cache.clear()
                # Шаблонами пользуется автор
                response3 = self.authorized_author.get(adress)
                self.assertTemplateUsed(response3, template)

    def test_valuer_url_create_template(self):
        # Доступно авторизированному / создание поста
        response = self.authorized_client.get('/create/')
        self.assertTemplateUsed(response, 'posts/create_post.html')
        # Перенаправляет неавторизованного юзера
        response2 = self.client.get('/create/')
        self.assertEqual(response2.status_code, HTTPStatus.FOUND)

    def test_noname_url_error(self):
        url = 'unexisting_page/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Юзером
        response2 = self.authorized_client.get(url)
        self.assertEqual(response2.status_code, HTTPStatus.NOT_FOUND)
        # Автором
        response3 = self.authorized_author.get(url)
        self.assertEqual(response3.status_code, HTTPStatus.NOT_FOUND)

    def test_only_author_edit_post(self):
        # Только автор может редактировать свой пост
        # Остальные перенаправляются на другую страницу
        # Авторизированный не автор поста -> перенаправление
        response = self.authorized_client.get(
            f'/posts/{PostURLTests.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        # Гость -> перенаправление
        response2 = self.client.get(f'/posts/{PostURLTests.post.pk}/edit/')
        self.assertEqual(response2.status_code, HTTPStatus.FOUND)
        # Автор редактирование
        response3 = self.authorized_author.get(
            f'/posts/{PostURLTests.post.pk}/edit/')
        self.assertEqual(response3.status_code, HTTPStatus.OK)
