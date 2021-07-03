# Generated by Django 3.1 on 2020-08-26 12:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0003_auto_20200826_1057"),
    ]

    operations = [
        migrations.AddField(
            model_name="defaults",
            name="is_sla_configured",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="defaults",
            name="track_ip",
            field=models.GenericIPAddressField(null=True),
        ),
    ]
