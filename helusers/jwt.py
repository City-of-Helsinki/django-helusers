try:
    from ._rest_framework_jwt_impl import (JWTAuthentication,
                                           get_user_id_from_payload_handler,
                                           patch_jwt_settings)
except ImportError:
    pass

from django.utils.functional import cached_property
from jose import jwt

from .settings import api_token_auth_settings


class ValidationError(Exception):
    pass


class JWT:
    def __init__(self, encoded_jwt):
        """The constructor checks that a JWT can be extracted from the
        provided input but it doesn't validate it in any way. If the
        input is invalid, an exception is raised."""
        self._encoded_jwt = encoded_jwt
        self._claims = jwt.get_unverified_claims(encoded_jwt)

    def validate(self, keys, audience):
        """Verifies the JWT's signature using the provided keys,
        and validates the claims, raising an exception if anything fails."""

        options = {
            "verify_aud": False,
            "require_exp": True,
        }

        jwt.decode(self._encoded_jwt, keys, options=options)

        claims = self.claims

        if "aud" not in claims:
            raise ValidationError("Missing required 'aud' claim.")

        claim_audiences = claims["aud"]
        if isinstance(claim_audiences, str):
            claim_audiences = {claim_audiences}
        if isinstance(audience, str):
            audience = {audience}
        if len(set(audience).intersection(claim_audiences)) == 0:
            raise ValidationError("Invalid audience.")

    @property
    def issuer(self):
        """Returns the "iss" claim value."""
        return self.claims["iss"]

    @property
    def claims(self):
        """Returns all the claims of the JWT as a dictionary."""
        return self._claims

    def has_api_scope_with_prefix(self, prefix):
        """Checks if there is an API scope with the given prefix.
        The name of the claims field where API scopes are looked for is
        determined by the OIDC_API_TOKEN_AUTH['API_AUTHORIZATION_FIELD']
        setting."""
        return any(
            x == prefix or x.startswith(prefix + ".")
            for x in self._authorized_api_scopes
        )

    @cached_property
    def _authorized_api_scopes(self):
        def is_list_of_non_empty_strings(value):
            return isinstance(value, list) and all(
                isinstance(x, str) and x for x in value
            )

        api_scopes = self.claims.get(api_token_auth_settings.API_AUTHORIZATION_FIELD)
        return set(api_scopes) if is_list_of_non_empty_strings(api_scopes) else set()
