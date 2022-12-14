# Generated by Django 4.1.2 on 2022-10-11 15:16

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserAttr",
            fields=[
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        serialize=False,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Пользователь",
                    ),
                ),
                (
                    "color",
                    models.CharField(
                        default="#75dfff", max_length=7, verbose_name="Цвет"
                    ),
                ),
                (
                    "openObjectsInNewWindow",
                    models.BooleanField(
                        default=False, verbose_name="Открывать объекты в новом окне"
                    ),
                ),
            ],
            options={
                "verbose_name": "Атрибуты пользователей",
                "verbose_name_plural": "Атрибуты пользователей",
            },
        ),
        migrations.CreateModel(
            name="UserAction",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "moment",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="Дата"
                    ),
                ),
                (
                    "object",
                    models.CharField(
                        blank=True, max_length=255, null=True, verbose_name="Объект"
                    ),
                ),
                (
                    "msg",
                    models.CharField(
                        blank=True, max_length=255, null=True, verbose_name="Действие"
                    ),
                ),
                ("warnLvl", models.IntegerField(default=0, verbose_name="Важность")),
                (
                    "link",
                    models.CharField(
                        blank=True, max_length=255, null=True, verbose_name="Ссылка"
                    ),
                ),
                (
                    "diff",
                    models.CharField(
                        blank=True, max_length=1023, null=True, verbose_name="Изменение"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Пользователь",
                    ),
                ),
            ],
            options={
                "verbose_name": "Действие пользователя",
                "verbose_name_plural": "Действия пользователей",
                "ordering": ["-moment"],
            },
        ),
    ]
