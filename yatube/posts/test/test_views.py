from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from yatube.settings import COUNT_LISTS

from ..models import Follow, Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовая группа',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        # Авторизуем автора
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_check_namespace_name(self):
        # Во view-функциях используются правильные html-шаблоны
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': f'{PostPagesTests.group.slug}'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': f'{PostPagesTests.user}'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{PostPagesTests.post.pk}'}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{PostPagesTests.post.pk}'}
            ): 'posts/create_post.html',
        }
        for namespace, templates in templates_pages_names.items():
            with self.subTest(namespace=namespace):
                # Автор может пользоваться всеми шаблонами
                response = self.authorized_client.get(namespace)
                self.assertTemplateUsed(response, templates)

    def test_page_show_correct_context(self):
        # Проверяем содержимое страниц: Index, Group_list, profile
        list_reveres = {
            reverse('posts:index'): 'Проверим, что отобразит главная страница',
            reverse(
                'posts:group_list', kwargs={
                    'slug': f'{PostPagesTests.group.slug}'}
            ): 'Проверим, что отобразит страница группы',
            reverse(
                'posts:profile', kwargs={
                    'username': f'{PostPagesTests.post.author}'}
            ): 'Проверим, что отобразит профайл',
        }
        for namespace in list_reveres.keys():
            with self.subTest(namespace=namespace):
                response = self.client.get(namespace)
                self.assertEqual(
                    response.context['page_obj'][0].id, PostPagesTests.post.id)
                self.assertEqual(
                    response.context[
                        'page_obj'][0].text, PostPagesTests.post.text)
                self.assertEqual(
                    response.context[
                        'page_obj'][0].group, PostPagesTests.group)
                self.assertEqual(
                    response.context[
                        'page_obj'][0].author, PostPagesTests.user)

    def test_post_detail_pages_show_correct_context(self):
        # Контекст для пост-детейл
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': f'{PostPagesTests.post.pk}'}))
        self.assertEqual(response.context.get(
            'post').text, PostPagesTests.post.text)
        self.assertEqual(response.context.get(
            'post').id, PostPagesTests.post.id)

    def test_create_pages_show_correct_context(self):
        # Контекст для создания поста
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_creat_post(self):
        # Создаем пост и проверяем попал ли он:
        # На главную страницу, профайл, группу
        post_count = Post.objects.count()
        user = User.objects.create_user(username='TestUser')
        group = Group.objects.create(
            title='Тестовая группа 2',
            slug='slug2',
            description='Тестовое описание 2',
        )
        post = Post.objects.create(
            text='Тестовая группа 2',
            author=user,
            group=group,
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        list_reveres = {
            reverse('posts:index'): 'Проверим, что отобразит главная страница',
            reverse(
                'posts:group_list', kwargs={'slug': f'{group.slug}'}
            ): 'Проверим, что отобразит страница группы',
            reverse(
                'posts:profile', kwargs={'username': f'{post.author}'}
            ): 'Проверим, что отобразит профайл',
        }
        for namespace in list_reveres.keys():
            with self.subTest(namespace=namespace):
                response = self.client.get(namespace)
                self.assertEqual(
                    response.context['page_obj'][0].id, post.id)
                self.assertEqual(
                    response.context['page_obj'][0].text, post.text)
                self.assertEqual(
                    response.context['page_obj'][0].group, post.group)

    def test_post_edit_pages_show_correct_context(self):
        # Контекст для редактирования поста
        response = self.authorized_client.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': f'{PostPagesTests.post.id}'}))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_un_auth_comment(self):
        test_post = Post.objects.create(
            text='text for test post',
            author=PostPagesTests.user
        )
        comment = 'text for comment'
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': test_post.id}),
            {'text': comment}
        )
        response = self.authorized_client.get(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': test_post.id}), follow=True)
        self.assertContains(response, comment)

    def test_cache_page(self):
        url = reverse('posts:index')
        post_new = Post.objects.create(
            text='Кэш',
            author=PostPagesTests.user
        )
        check_home_page = self.authorized_client.get(url)
        self.assertEqual(check_home_page.context[
            'page_obj'][0].text, post_new.text)
        post_new.delete()
        check_home_page2 = self.authorized_client.get(url)
        self.assertEqual(check_home_page2.context, None)
        cache.clear()
        check_home_page3 = self.authorized_client.get(url)
        self.assertEqual(check_home_page3.context[
            'page_obj'][0].text, PostPagesTests.post.text)

    def test_user_follow(self):
        new_user = User.objects.create(username='подписчик')
        response = self.authorized_client.post(
            reverse('posts:profile_follow', args=[new_user]), follow=True)
        self.assertEqual(response.status_code, 200)
        find_follow = Follow.objects.get(
            user=PostPagesTests.user, author=new_user)
        self.assertTrue(find_follow)
        self.assertEqual(PostPagesTests.user, find_follow.user)
        self.assertEqual(PostPagesTests.user.follower.count(), 1)
        self.assertEqual(new_user, find_follow.author)

    def test_user_unfollow(self):
        new_user = User.objects.create(username='юзер')
        Follow.objects.create(
            user=PostPagesTests.user, author=new_user)
        response = self.authorized_client.post(
            reverse('posts:profile_unfollow', args=[new_user]), follow=True)
        self.assertEqual(response.status_code, 200)
        find_follow = Follow.objects.exists()
        self.assertFalse(find_follow)
        self.assertEqual(PostPagesTests.user.follower.count(), 0)

    def test_new_post_follow_and_unfollow(self):
        new_user = User.objects.create(username='юзер')
        Post.objects.create(text='Текст', author=new_user)
        post_last = Post.objects.first()
        response = self.authorized_client.get(
            reverse('posts:profile_follow', args=[new_user]), follow=True)
        self.assertContains(response, post_last.text)
        text = 'ещё один пост'
        Post.objects.create(
            text=text, author=PostPagesTests.user)
        response2 = self.authorized_client.get(
            reverse('posts:profile_follow', args=[new_user]), follow=True)
        self.assertNotContains(response2, text)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.userZ = User.objects.create(username='Paginator')
        cls.groupZ = Group.objects.create(
            title='Paginator1',
            slug='Paginator1',
            description='Paginator about'
        )
        cls.create_list = []
        for post in range(0, 13):
            cls.create_list.append(Post.objects.create(
                author=cls.userZ,
                text='text text{post}',
                group=cls.groupZ
            ))

    def test_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), COUNT_LISTS)

    def test_second_page_contains_three_records(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(
            response.context['page_obj']
        ), Post.objects.count() - COUNT_LISTS)
