try:
    from ._oidc_auth_impl import ApiTokenAuthentication, resolve_user
except ImportError:
    pass


from .authz import UserAuthorization
from .jwt import JWT
from .user_utils import get_or_create_user


class AuthenticationError(Exception):
    pass


class RequestJWTAuthentication:
    def __init__(self, key_provider=None):
        """
        key_provider: a callable that provides public keys for an issuer.
        """
        self._key_provider = key_provider

    def authenticate(self, request):
        """Looks for a JWT from the request's "Authorization" header and verifies it.
        If verification passes, takes a user's id from the JWT's "sub" claim.
        Creates a User if it doesn't already exist. On success returns the User
        and a UserAuthorization object as a (User, UserAuthorization) tuple.
        Raises an AuthenticationError on authentication failure."""
        auth = request.headers["Authorization"].split()
        jwt_value = auth[1]

        jwt = JWT(jwt_value)
        keys = self._key_provider(jwt.issuer)
        try:
            jwt.validate(keys)
        except Exception:
            raise AuthenticationError("JWT verification failed.")

        claims = jwt.claims
        user = get_or_create_user(claims, oidc=True)
        auth = UserAuthorization(user, claims)

        return (user, auth)
