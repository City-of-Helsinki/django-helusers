from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _
from rest_framework import exceptions


def get_or_create_user(payload):
    user_id = payload.get('sub')
    if not user_id:
        msg = _('Invalid payload.')
        raise exceptions.AuthenticationFailed(msg)

    user_model = get_user_model()

    try:
        user = user_model.objects.get(uuid=user_id)
    except user_model.DoesNotExist:
        user = user_model(uuid=user_id)
        user.set_unusable_password()

    changed = populate_user(user, payload)
    if changed:
        user.save()

    ad_groups = payload.get('ad_groups', None)
    # Only update AD groups if it's a list of non-empty strings
    if isinstance(ad_groups, list) and (
            all([isinstance(x, str) and x for x in ad_groups])):
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
                email = EmailAddress(email=user.email.lower(), primary=True,
                                     user=user, verified=True)
                email.save()

    return user


def populate_user(user, data):
    user_model = get_user_model()

    exclude_fields = ['is_staff', 'password', 'is_superuser', 'id']
    user_fields = [f.name for f in user._meta.fields
                   if f.name not in exclude_fields]
    changed = False
    for field in user_fields:
        if field in data:
            val = data[field]
            if getattr(user, field) != val:
                setattr(user, field, val)
                changed = True

    # Make sure there are no duplicate usernames
    tries = 0
    other_users = user_model.objects.exclude(uuid=user.uuid)
    while other_users.filter(username=user.username).exists():
        user.username = "%s-%d" % (user.username, tries + 1)
        changed = True

    return changed
