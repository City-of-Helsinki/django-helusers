from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig
from django.utils.translation import gettext_lazy as _


class HelusersConfig(AppConfig):
    name = "helusers"
    verbose_name = _("Helsinki Users")
    default_auto_field = "django.db.models.AutoField"


class HelusersAdminConfig(AdminConfig):
    default_site = "helusers.admin_site.AdminSite"
