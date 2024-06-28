from django.contrib.admin.apps import AdminConfig

class HelusersAdminConfig(AdminConfig):
    default_site = "helusers.admin_site.AdminSite"
