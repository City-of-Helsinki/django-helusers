from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("helusers", "0001_add_ad_groups"),
    ]

    operations = [
        migrations.CreateModel(
            name="OIDCBackChannelLogoutEvent",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("iss", models.CharField(db_index=True, max_length=4096)),
                ("sub", models.CharField(blank=True, db_index=True, max_length=4096)),
                ("sid", models.CharField(blank=True, db_index=True, max_length=4096)),
            ],
            options={
                "verbose_name": "OIDC back channel logout event",
                "verbose_name_plural": "OIDC back channel logout events",
                "unique_together": {("iss", "sub", "sid")},
            },
        ),
    ]
