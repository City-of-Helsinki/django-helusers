from django.apps import AppConfig

from django.utils.translation import gettext_lazy as _


class HelusersConfig(AppConfig):
    name = "helusers"
    verbose_name = _("Helsinki Users")
    default_auto_field = "django.db.models.AutoField"
