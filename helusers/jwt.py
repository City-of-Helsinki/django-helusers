from django.utils.translation import ugettext as _
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework_jwt.settings import api_settings
from rest_framework import exceptions
import random

User = get_user_model()


def patch_jwt_settings():
    """Patch rest_framework_jwt authentication settings from allauth"""
    defaults = api_settings.defaults
    defaults['JWT_PAYLOAD_GET_USER_ID_HANDLER'] = 'helusers.jwt.get_user_id_from_payload_handler'

    if 'allauth.socialaccount' not in settings.INSTALLED_APPS:
        return

    from allauth.socialaccount.models import SocialApp
    try:
        app = SocialApp.objects.get(provider='helsinki')
    except SocialApp.DoesNotExist:
        return

    defaults['JWT_SECRET_KEY'] = app.secret
    defaults['JWT_AUDIENCE'] = app.client_id

# Disable automatic settings patching for now because it breaks Travis.
# patch_jwt_settings()

class JWTAuthentication(JSONWebTokenAuthentication):

    def populate_user(self, user, data):
        exclude_fields = ['is_staff', 'password', 'is_superuser', 'id']
        user_fields = [f.name for f in user._meta.fields if f.name not in exclude_fields]
        changed = False
        for field in user_fields:
            if field in data:
                val = data[field]
                if getattr(user, field) != val:
                    setattr(user, field, val)
                    changed = True

        # Make sure there are no duplicate usernames
        tries = 0
        while User.objects.filter(username=user.username).exclude(uuid=user.uuid).exists():
            user.username = "%s-%d" % (user.username, tries + 1)
            changed = True

        return changed

    def authenticate_credentials(self, payload):
        user_id = payload.get('sub')
        if not user_id:
            msg = _('Invalid payload.')
            raise exceptions.AuthenticationFailed(msg)

        try:
            user = User.objects.get(uuid=user_id)
        except User.DoesNotExist:
            user = User(uuid=user_id)
            user.set_unusable_password()

        changed = self.populate_user(user, payload)
        if changed:
            user.save()

        ad_groups = payload.get('ad_groups', None)
        # Only update AD groups if it's a list of non-empty strings
        if isinstance(ad_groups, list) and \
                all([isinstance(x, str) and len(x) for x in ad_groups]):
            user.update_ad_groups(ad_groups)

        # If allauth.socialaccount is installed, create the SocialAcount
        # that corresponds to this user. Otherwise logins through
        # allauth will not work for the user later on.
        if 'allauth.socialaccount' in settings.INSTALLED_APPS:
            from allauth.socialaccount.models import SocialAccount, EmailAddress

            args = {'provider': 'helsinki', 'uid': user_id}
            try:
                account = SocialAccount.objects.get(**args)
                assert account.user_id == user.id
            except SocialAccount.DoesNotExist:
                account = SocialAccount(**args)
                account.extra_data = payload
                account.user = user
                account.save()

                try:
                    email = EmailAddress.objects.get(email__iexact=user.email)
                    assert email.user == user
                except EmailAddress.DoesNotExist:
                    email = EmailAddress(email=user.email.lower(), primary=True, user=user,
                                         verified=True)
                    email.save()

        return super(JWTAuthentication, self).authenticate_credentials(payload)


def get_user_id_from_payload_handler(payload):
    return payload.get('sub')
