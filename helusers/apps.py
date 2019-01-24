from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.apps import AdminConfig


class HelusersConfig(AppConfig):
    name = 'helusers'
    verbose_name = _("Helsinki Users")


class HelusersAdminConfig(AdminConfig):
    default_site = 'helusers.admin.AdminSite'
