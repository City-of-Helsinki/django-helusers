from django.conf import settings as django_settings


def settings(request):
    ret = dict()
    ret['TUNNISTAMO_BASE_URL'] = getattr(django_settings, 'TUNNISTAMO_BASE_URL', None)
    return ret
