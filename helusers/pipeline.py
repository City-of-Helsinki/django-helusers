from django.contrib.auth import get_user_model
from .user_utils import update_user, get_or_create_user
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
