import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from django.db import transaction, IntegrityError
from uuid import UUID, uuid5

logger = logging.getLogger(__name__)

def oidc_to_user_data(payload):
    """
    Map OIDC claims to Django user fields.
    """
    payload = payload.copy()

    field_map = {
        'given_name': 'first_name',
        'family_name': 'last_name',
        'email': 'email',
    }
    ret = {}
    for token_attr, user_attr in field_map.items():
        if token_attr not in payload:
            continue
        ret[user_attr] = payload.pop(token_attr)
    ret.update(payload)

    return ret


def populate_user(user, data):
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

    return changed


def update_user(user, payload, oidc=False):
    if oidc:
        payload = oidc_to_user_data(payload)

    # Default is for Tunnistamo, Azure uses 'groups'
    group_claim_name = getattr(settings, 'HELUSERS_ADGROUPS_CLAIM', 'ad_groups')

    changed = populate_user(user, payload)
    if changed or not user.pk:
        user.save()

    logger.debug("checking for AD groups in claim `%s`", group_claim_name)

    ad_groups = payload.get(group_claim_name, None)
    logger.debug("AD groups found in claim: %s", ad_groups)
    # Only update AD groups if it's a list of non-empty strings
    if isinstance(ad_groups, list) and (
            all([isinstance(x, str) and x for x in ad_groups])):
        user.update_ad_groups(ad_groups)

# Critical section for user creation. It is quite possible that,
# for a new user, the first requests fired toward the API will race
# for creating the user. All but one of these will then fail.
def _try_create_or_update(user_id, payload, oidc):
    user_id = UUID(user_id)
    user_model = get_user_model()
    with transaction.atomic():
        try:
            user = user_model.objects.get(uuid=user_id)
        except user_model.DoesNotExist:
            user = user_model(uuid=user_id)
            user.set_unusable_password()
        update_user(user, payload, oidc)
    return user

def is_valid_uuid(uuid_to_test, version=None):
    try:
        uuid_obj = UUID(uuid_to_test, version=version)
    except ValueError:
        return False

    return str(uuid_obj) == uuid_to_test

def convert_to_uuid(convertable, namespace=None):
    # Our default, arbitrary, namespace
    if namespace is None:
        namespace = UUID('126c8382-ab0c-11ea-be22-8c8590573044')
    else:
        namespace = UUID(namespace)

    logger.debug("set namespace to %s", namespace)

    # several users expect this to be string, as if read
    # from a 'sub' field of a token
    generated_uuid = str(uuid5(namespace, convertable))

    logger.debug("generated UUID: %s to stand for non-UUID: %s", generated_uuid, convertable)

    return generated_uuid

def get_or_create_user(payload, oidc=False):
    user_id = payload.get('sub')
    if not user_id:
        msg = _('Invalid payload. sub missing')
        raise ValueError(msg)

    # django-helusers uses UUID as the primary key for the user
    # If the incoming token does not have UUID in the sub field,
    # we must synthesize one
    if not is_valid_uuid(user_id):
        # Maybe we have an Azure pairwise ID? Check for Azure tenant ID
        # in token and use that as UUID namespace if available
        namespace = payload.get('tid')
        user_id = convert_to_uuid(user_id, namespace)

    try_again = False
    try:
        user = _try_create_or_update(user_id, payload, oidc)
    except IntegrityError:
        # If we get an integrity error, it probably meant a race
        # condition with another process. Another attempt should
        # succeed.
        try_again = True
    if try_again:
        # We try again without catching exceptions this time.
        user = _try_create_or_update(user_id, payload, oidc)

    # If allauth.socialaccount is installed, create the SocialAcount
    # that corresponds to this user. Otherwise logins through
    # allauth will not work for the user later on.
    if 'allauth.socialaccount' in settings.INSTALLED_APPS:
        from allauth.socialaccount.models import SocialAccount, EmailAddress

        if oidc:
            provider_name = 'helsinki_oidc'
        else:
            provider_name = 'helsinki'
        args = {'provider': provider_name, 'uid': user_id}
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
