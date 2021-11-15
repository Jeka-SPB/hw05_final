from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
        )

    def test_models_have_correct_object_names_post(self):
        post = PostModelTest.post
        post_text = post.text
        self.assertEqual(post_text, str(post))

    def test_models_have_correct_object_names_group(self):
        group = PostModelTest.group
        group_title = group.title
        self.assertEqual(group_title, str(group))

    def test_pub_date_post_label(self):
        """verbose_name поля title совпадает с ожидаемым."""
        post = PostModelTest.post
        # Получаем из свойста класса Task значение verbose_name для title
        verbose = post._meta.get_field('pub_date').verbose_name
        self.assertEqual(verbose, 'Дата публикации')

    def test_post_group_help_text(self):
        post = PostModelTest.post
        help_text = post._meta.get_field('group').help_text
        self.assertEqual(help_text, 'Выберите группу')
