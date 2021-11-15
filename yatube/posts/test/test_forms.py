import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostvalidTests(TestCase):
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
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='slug2',
            description='Тестовое описание2',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Авторизуем автора
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Регаем пользователя
        self.user2 = User.objects.create_user(username='auth1')
        self.authorized2_client = Client()
        self.authorized2_client.force_login(self.user2)

    def test_new_post_in_db(self):
        # Проверяем создается ли новый пост
        post_count = Post.objects.count()
        form_post = {
            'text': 'Автор создал пост в бд',
            'group': PostvalidTests.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'), data=form_post, follow=True)
        self.assertRedirects(response, f'/profile/{self.user}/')
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        new_post = Post.objects.latest('id')
        self.assertEqual(new_post.text, form_post.get('text'))
        self.assertEqual(new_post.group.pk, form_post.get('group'))

    def test_guest_new_post_in_db(self):
        # Гость не может создать пост
        post_count = Post.objects.count()
        form_post = {
            'text': 'Гость пытается создать пост',
        }
        guest = self.client.post(reverse(
            'posts:post_create'), data=form_post, follow=True)
        self.assertTrue(guest.redirect_chain)
        self.assertRedirects(guest, '/auth/login/?next=/create/')
        self.assertEqual(Post.objects.count(), post_count)

    def test_user_new_post_in_db(self):
        # Пользователь создает пост в бд
        post_count = Post.objects.count()
        form_post = {
            'text': 'User создал пост в бд',
        }
        user = self.authorized2_client.post(
            reverse('posts:post_create'), data=form_post, follow=True)
        self.assertRedirects(user, f'/profile/{self.user2}/')
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(Post.objects.first(), user.context['page_obj'][0])
        self.assertEqual(Post.objects.latest('id').text, form_post.get('text'))

    def test_post_edit(self):
        # Проверяем редактируется пост Автором
        post_count = Post.objects.count()
        form_post = {
            'text': 'Новый текст author',
            'group': PostvalidTests.group2.pk,
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit', args=(f'{PostvalidTests.post.pk}')
            ), data=form_post)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Post.objects.count(), post_count)
        post_edit = Post.objects.get(pk=PostvalidTests.post.pk)
        self.assertEqual(post_edit.text, form_post.get('text'))
        self.assertEqual(post_edit.group.pk, form_post.get('group'))

    def test_guest_post_edit(self):
        # Гость не может редактировать пост
        form_post = {
            'text': 'Гость не может редактировать пост',
        }
        guest = self.client.post(reverse(
            'posts:post_edit', args=(f'{PostvalidTests.post.pk}')
        ), data=form_post, follow=True)
        self.assertTrue(guest.redirect_chain)
        self.assertRedirects(
            guest, (f'/auth/login/?next='
                    f'/posts/{PostvalidTests.post.pk}/edit/'))
        post_edit = Post.objects.get(pk=PostvalidTests.post.pk)
        self.assertNotEqual(post_edit.text, form_post.get('text'))

    def test_user_post_edit(self):
        # Пользователь не может редактировать пост другого автора
        form_post = {
            'text': 'User редактирует чужой пост',
        }
        user = self.authorized2_client.post(
            reverse(
                'posts:post_edit', args=(f'{PostvalidTests.post.pk}')
            ), data=form_post, follow=True)
        self.assertRedirects(user, f'/posts/{PostvalidTests.post.pk}/')
        post_edit = Post.objects.get(pk=PostvalidTests.post.pk)
        self.assertNotEqual(post_edit.text, form_post.get('text'))

    def test_image_create_adn_context(self):
        # В одном тесте проверяем что мы можем создавать пост с картинкой
        # и проверим её отображение на страницах
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_post = {
            'title': 'Это поле мы тестить не будем',
            'text': 'Это поле мы тестить не будем',
            'image': uploaded,
            'group': PostvalidTests.group2.pk,
        }
        # Другими тестами мы проверили кто что может создавать и редактировать
        # Допустим создал юзер
        user = self.authorized2_client.post(
            reverse('posts:post_create'), data=form_post, follow=True)
        # Проверим что количество постов увеличилось на 1
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(Post.objects.first(), user.context['page_obj'][0])
        # Теперь проверим что картинка отображается
        # на страницах :
        # профайла,
        # группы,
        # на отдельную страницу поста
        last_creat_post = Post.objects.latest('id')
        list_reveres = {
            reverse(
                'posts:index'
            ): 'Проверим, что отобразит главная страница',
            reverse(
                'posts:group_list', kwargs={
                    'slug': f'{last_creat_post.group.slug}'}
            ): 'Проверим, что отобразит страница группы',
            reverse(
                'posts:profile', kwargs={
                    'username': f'{last_creat_post.author}'}
            ): 'Проверим, что отобразит профайл',
        }
        for namespace in list_reveres.keys():
            with self.subTest(namespace=namespace):
                response = self.authorized2_client.get(namespace)
                self.assertEqual(
                    response.context[
                        'page_obj'][0].image, last_creat_post.image)
        # Отдельно для пост детейл там нет пагинатора
        post_detail = self.authorized2_client.get(reverse(
            'posts:post_detail', kwargs={
                'post_id': f'{last_creat_post.pk}'}
        ))
        self.assertEqual(
            post_detail.context.get('post').image, last_creat_post.image)

    def test_comment_guest(self):
        comment_count = Comment.objects.count()
        form = {
            'text': 'Тестовый текст'
        }
        guest = self.client.post(reverse('posts:add_comment', kwargs={
            'post_id': f'{PostvalidTests.post.pk}'}
        ), data=form)
        self.assertEqual(guest.status_code, HTTPStatus.FOUND)
        self.assertEqual(comment_count, 0)

    def test_comment_authorized_client(self):
        # На данный момент у нас нет комментариев, поэтому тут 0
        comment_count = Comment.objects.count()
        form = {
            'text': 'Тестовый коммент'
        }
        user = self.authorized2_client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': f'{PostvalidTests.post.pk}'}
            ), data=form
        )
        # Проверим что мы создали коммент
        self.assertEqual(comment_count + 1, Comment.objects.count())
        self.assertEqual(user.status_code, HTTPStatus.FOUND)
        last_comment = Comment.objects.latest('id')
        self.assertEqual(last_comment.text, form.get('text'))
        # Добавим проверку что он появился на странице
        userr = self.authorized2_client.get(reverse(
            'posts:post_detail', kwargs={
                'post_id': f'{PostvalidTests.post.pk}'})
        )
        self.assertEqual(
            userr.context.get('comments')[0].text, last_comment.text)
