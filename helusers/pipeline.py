import logging
import requests
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.conf import settings
from .user_utils import get_or_create_user
from .utils import uuid_to_username
from .tunnistamo_oidc import TunnistamoOIDCAuth


User = get_user_model()
logger = logging.getLogger(__name__)


def ensure_uuid_match(details, backend, response, user=None, *args, **kwargs):
    if not isinstance(backend, TunnistamoOIDCAuth):
        return

    user = user or details.get('user')
    if user is not None:
        if user.uuid != details.get('uid') or response.get('sub'):
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


def fetch_api_tokens(details, backend, response, user=None, social=None, request=None, *args, **kwargs):
    if not isinstance(backend, TunnistamoOIDCAuth):
        return
    if not user or not user.is_authenticated or not social:
        return

    scopes = set(backend.get_scope())
    # slightly ghetto-style filtering, but it works for now
    api_scopes = {s for s in scopes if s.startswith('https://')}
    tunnistamo_scopes = scopes - api_scopes

    request.session['access_token_scope'] = list(tunnistamo_scopes)
    request.session['access_token'] = response['access_token']
    expires_at = datetime.now() + timedelta(seconds=response['expires_in'])
    request.session['access_token_expires_at'] = expires_at
    expires_at_ts = int(expires_at.timestamp()) * 1000
    request.session['access_token_expires_at_ts'] = expires_at_ts

    if not api_scopes:
        return

    logger.info('Retrieving API tokens for scopes %s' % ' '.join(api_scopes))

    headers = {'Authorization': 'Bearer %s' % social.extra_data['access_token']}
    url = settings.TUNNISTAMO_BASE_URL + '/api-tokens/'
    resp = requests.post(url, headers=headers)
    if resp.status_code != 200:
        logger.error('Unable to get API tokens: HTTP %d' % (resp.status_code))
        return
    request.session['api_tokens'] = resp.json()
