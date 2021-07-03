# Generated by Django 3.1.2 on 2020-11-05 08:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0013_defaults_dns"),
    ]

    operations = [
        migrations.AlterField(
            model_name="hosts",
            name="ip",
            field=models.CharField(max_length=15),
        ),
        migrations.AlterField(
            model_name="hosts",
            name="name",
            field=models.CharField(max_length=30, primary_key=True, serialize=False),
        ),
    ]
