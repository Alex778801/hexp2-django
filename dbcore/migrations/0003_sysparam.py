# Generated by Django 4.1.2 on 2022-11-08 09:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dbcore", "0002_alter_agent_acl_alter_costtype_acl_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="SysParam",
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
                ("name", models.CharField(max_length=100, verbose_name="Название")),
                ("value", models.CharField(max_length=1000, verbose_name="Значение")),
            ],
        ),
    ]
