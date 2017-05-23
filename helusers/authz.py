from django.utils.functional import cached_property

from .settings import api_settings


class UserAuthorization(object):
    def __init__(self, user, id_token_payload, settings=None):
        """
        Initialize authorization info from user and ID token payload.
        """
        self.user = user
        self.data = id_token_payload
        self.settings = settings or api_settings

    def has_api_scopes(self, *api_scopes):
        """
        Test if all given API scopes are authorized.

        :type api_scopes: list[str]
        :param api_scopes: The API scopes to test

        :rtype: bool|None
        :return:
          True or False, if the ID token has the API scopes field set,
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
            x == prefix or x.startswith(prefix + '.')
            for x in self._authorized_api_scopes)

    def has_ad_groups(self, *ad_groups):
        """
        Test if all given AD groups are authorized.

        :type ad_groups: list[str]
        :param ad_groups: The AD groups to test

        :rtype: bool|None
        :return:
          True or False, if the ID token has the API scopes field set,
          otherwise None
        """
        if self._ad_groups is None:
            return None
        return all((x.lower() in self._ad_groups) for x in ad_groups)

    @cached_property
    def _authorized_api_scopes(self):
        api_scopes = self.data.get(self.settings.API_AUTHORIZATION_FIELD)
        return (set(api_scopes)
                if is_list_of_non_empty_strings(api_scopes) else None)

    @cached_property
    def _ad_groups(self, id_token_payload):
        ad_groups = self.data.get(self.settings.AD_GROUPS_FIELD)
        return (set(x.lower() for x in ad_groups)
                if is_list_of_non_empty_strings(ad_groups) else None)


def is_list_of_non_empty_strings(value):
    if not isinstance(value, list):
        return False
    return all(isinstance(x, str) and x for x in value)
