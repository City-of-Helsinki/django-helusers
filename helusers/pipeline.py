from django.contrib.auth import get_user_model
from .user_utils import get_or_create_user
from .utils import uuid_to_username
from .tunnistamo_oidc import TunnistamoOIDCAuth


User = get_user_model()


def ensure_uuid_match(details, backend, response, *args, **kwargs):
    if not isinstance(backend, TunnistamoOIDCAuth):
        return

    user = details.get('user')
    if user is not None:
        if user.uuid != details['uid']:
            return {'user': None}


def get_username(details, backend, response, *args, **kwargs):
    """Sets the `username` argument.

    If the user exists already, use the existing username. Otherwise
    generate username from the `new_uuid` using the
    `helusers.utils.uuid_to_username` function.
    """

    user = details.get('user')
    if not user:
        user_uuid = kwargs.get('uid')
        if not user_uuid:
            return

        username = uuid_to_username(user_uuid)
    else:
        username = user.username

    return {
        'username': username
    }


def create_or_update_user(details, backend, response, user=None, *args, **kwargs):
    response = response.copy()
    username = kwargs.get('username')
    if username:
        response['username'] = username

    user = get_or_create_user(response, oidc=True)
    return {
        'user': user
    }


def store_end_session_url(details, backend, response, user=None, *args, **kwargs):
    if not user or not user.is_authenticated:
        return

    if not hasattr(backend, 'get_end_session_url'):
        return
    request = kwargs['request']
    end_session_url = backend.get_end_session_url(request, response['id_token'])
    if not end_session_url:
        return

    request.session['social_auth_end_session_url'] = end_session_url
    if 'id_token' in response:
        request.session['social_auth_id_token'] = response['id_token']
