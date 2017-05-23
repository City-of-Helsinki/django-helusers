from rest_framework.permissions import BasePermission, SAFE_METHODS

from .authz import UserAuthorization
from .settings import api_settings


class ApiScopePermission(BasePermission):
    """
    API scope based permission checker.
    """
    def __init__(self, settings=None):
        self.settings = settings or api_settings

    def has_permission(self, request, view):
        auth = getattr(request, 'auth', None)
        if isinstance(auth, UserAuthorization):
            api_scope = self.settings.API_SCOPE_PREFIX
            if auth.has_api_scopes(api_scope):
                return True
            if request.method in SAFE_METHODS:
                if auth.has_api_scopes(api_scope + '.readonly'):
                    return True
        return False

    def has_object_permission(self, request, view, obj):
        if not self.has_permission(request, view):
            return False
        return super(ApiScopePermission, self).has_object_permission(
            request, view, obj)
