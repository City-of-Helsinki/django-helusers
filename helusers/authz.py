from django.utils.functional import cached_property

from .settings import api_token_auth_settings
from .utils import get_scopes_from_claims


class UserAuthorization(object):
    def __init__(self, user, api_token_payload, settings=None):
        """
        Initialize authorization info from user and API Token payload.
        """
        self.user = user
        self.data = api_token_payload
        self.settings = settings or api_token_auth_settings

    def has_api_scopes(self, *api_scopes):
        """
        Test if all given API scopes are authorized.

        :type api_scopes: list[str]
        :param api_scopes: The API scopes to test

        :rtype: bool|None
        :return:
          True or False, if the API Token has the API scopes field set,
          otherwise None
        """
        if self._authorized_api_scopes is None:
            return None
        return all((x in self._authorized_api_scopes) for x in api_scopes)

    def has_api_scope_with_prefix(self, prefix):
        """
        Test if there is an API scope with the given prefix.

        :rtype: bool|None
        """
        if self._authorized_api_scopes is None:
            return None
        return any(
            x == prefix or x.startswith(prefix + ".")
            for x in self._authorized_api_scopes
        )

    @cached_property
    def _authorized_api_scopes(self):
        return get_scopes_from_claims(self.settings.API_AUTHORIZATION_FIELD, self.data)
