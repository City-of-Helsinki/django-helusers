from django.apps import apps
from django.contrib import admin
from django.conf import settings
from django.utils.translation import ugettext_lazy
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import autodiscover_modules


if hasattr(settings, 'SITE_TYPE'):
    if settings.SITE_TYPE not in ('dev', 'test', 'production'):
        raise ImproperlyConfigured("SITE_TYPE must be either 'dev', 'test' or 'production'")


class AdminSite(admin.AdminSite):
    login_template = "admin/hel_login.html"

    def __init__(self, *args, **kwargs):
        super(AdminSite, self).__init__(*args, **kwargs)

    @property
    def site_header(self):
        Site = apps.get_model(app_label='sites', model_name='Site')
        site = Site.objects.get_current()
        return ugettext_lazy("%(site_name)s admin") % {'site_name': site.name}

    def each_context(self, request):
        ret = super(AdminSite, self).each_context(request)
        ret['site_type'] = getattr(settings, 'SITE_TYPE', 'dev')
        ret['redirect_path'] = request.GET.get('next', None)
        return ret


site = AdminSite()
site._registry.update(admin.site._registry)
# Monkeypatch the default admin site with the custom one
default_admin_site = admin.site
admin.site = site

# Copy the admin registrations from the default site
site._registry.update(default_admin_site._registry)

def autodiscover():
    autodiscover_modules('admin', register_to=site)
