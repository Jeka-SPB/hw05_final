# Generated by Django 2.2.19 on 2021-10-29 06:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0006_auto_20211009_1155'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ['-pub_date']},
        ),
        migrations.AlterField(
            model_name='post',
            name='text',
            field=models.TextField(help_text='Извольте ввести текст', verbose_name='Текст поста'),
        ),
    ]
