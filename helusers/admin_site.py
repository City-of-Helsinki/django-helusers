import django
from django.apps import apps
from django.contrib import admin
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy
from django.views.decorators.cache import never_cache


if hasattr(settings, 'SITE_TYPE'):
    if settings.SITE_TYPE not in ('dev', 'test', 'production'):
        raise ImproperlyConfigured("SITE_TYPE must be either 'dev', 'test' or 'production'")


PROVIDERS = (
    ('helusers.providers.helsinki', 'helsinki_login'),
    ('helusers.providers.helsinki_oidc', 'helsinki_oidc_login')
)


class AdminSite(admin.AdminSite):
    login_template = "admin/hel_login.html"

    def __init__(self, *args, **kwargs):
        super(AdminSite, self).__init__(*args, **kwargs)

    @property
    def site_header(self):
        if 'django.contrib.sites' in settings.INSTALLED_APPS:
            Site = apps.get_model(app_label='sites', model_name='Site')
            site = Site.objects.get_current()
            site_name = site.name
        elif hasattr(settings, 'WAGTAIL_SITE_NAME'):
            site_name = settings.WAGTAIL_SITE_NAME
        else:
            return ugettext_lazy("Django admin")
        return ugettext_lazy("%(site_name)s admin") % {'site_name': site_name}

    def each_context(self, request):
        ret = super(AdminSite, self).each_context(request)
        ret['site_type'] = getattr(settings, 'SITE_TYPE', 'dev')
        ret['redirect_path'] = request.GET.get('next', None)
        provider_installed = False
        if 'helusers.tunnistamo_oidc.TunnistamoOIDCAuth' in settings.AUTHENTICATION_BACKENDS:
            provider_installed = True
            login_url = reverse('helusers:auth_login')
            logout_url = reverse('helusers:auth_logout')
        else:
            for provider, login_view in PROVIDERS:
                if provider not in settings.INSTALLED_APPS:
                    continue
                provider_installed = True
                login_url = reverse(login_view)
                break
            logout_url = None

        ret['helsinki_provider_installed'] = provider_installed
        if provider_installed:
            ret['helsinki_login_url'] = login_url
            ret['helsinki_logout_url'] = logout_url

        ret['grappelli_installed'] = 'grappelli' in settings.INSTALLED_APPS
        if ret['grappelli_installed']:
            ret['grappelli_admin_title'] = self.site_header
            ret['base_site_template'] = 'admin/base_site_grappelli.html'
        else:
            ret['base_site_template'] = 'admin/base_site_default.html'

        ret['password_login_disabled'] = getattr(settings, 'HELUSERS_PASSWORD_LOGIN_DISABLED', False)

        return ret

    @never_cache
    def logout(self, request, extra_context=None):
        if request.session and request.session.get('social_auth_end_session_url'):
            logout_url = reverse('helusers:auth_logout')
            return HttpResponseRedirect(logout_url)
        return super().logout(request, extra_context)


# Django versions starting from 2.1 support overriding the default admin
# site, so monkeypatching is not needed.
if django.VERSION[0:2] < (2, 1):
    site = AdminSite()
    site._registry.update(admin.site._registry)
    default_admin_site = admin.site
    # Monkeypatch the default admin site with the custom one
    admin.site = site
    admin.sites.site = site
