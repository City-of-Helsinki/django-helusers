from .utils import get_scopes_from_claims

try:
    from ._rest_framework_jwt_impl import (  # noqa: F401
        get_user_id_from_payload_handler,
        JWTAuthentication,
        patch_jwt_settings,
    )
except ImportError:
    pass

from django.utils.functional import cached_property
from jose import jwt

from .models import OIDCBackChannelLogoutEvent
from .settings import api_token_auth_settings

_NOT_PROVIDED = object()


class ValidationError(Exception):
    pass


class JWT:
    def __init__(self, encoded_jwt, settings=None):
        """The constructor checks that a JWT can be extracted from the
        provided input but it doesn't validate it in any way. If the
        input is invalid, an exception is raised."""
        self._encoded_jwt = encoded_jwt
        self._claims = jwt.get_unverified_claims(encoded_jwt)
        self.settings = settings or api_token_auth_settings

    def validate(self, keys, audience, required_claims=_NOT_PROVIDED):
        """Verifies the JWT's signature using the provided keys,
        and validates the claims, raising an exception if anything fails.
        Required claims can be specified using the required_claims argument
        and it defaults to ["aud", "exp"]."""

        if required_claims is _NOT_PROVIDED:
            required_claims = ["aud", "exp"]

        options = {
            "verify_aud": False,
        }

        require_aud = "aud" in required_claims
        required_claims.remove("aud")

        for required_claim in required_claims:
            options[f"require_{required_claim}"] = True

        jwt.decode(self._encoded_jwt, keys, options=options)

        claims = self.claims
        if require_aud and "aud" not in claims:
            raise ValidationError("Missing required 'aud' claim.")

        if "aud" in claims:
            claim_audiences = claims["aud"]
            if isinstance(claim_audiences, str):
                claim_audiences = {claim_audiences}
            if isinstance(audience, str):
                audience = {audience}
            if len(set(audience).intersection(claim_audiences)) == 0:
                raise ValidationError("Invalid audience.")

    def validate_issuer(self):
        try:
            issuer = self.issuer
        except KeyError:
            raise ValidationError('Required "iss" claim is missing.')

        issuers = self.settings.ISSUER
        if isinstance(issuers, str):
            issuers = [issuers]

        if issuer not in issuers:
            raise ValidationError("Unknown JWT issuer {}.".format(issuer))

    def validate_api_scope(self):
        if not self.settings.REQUIRE_API_SCOPE_FOR_AUTHENTICATION:
            return

        api_scopes = self.settings.API_SCOPE_PREFIX
        if isinstance(api_scopes, str):
            api_scopes = [api_scopes]

        if not any(
            [self.has_api_scope_with_prefix(api_scope) for api_scope in api_scopes]
        ):
            raise ValidationError(
                'Not authorized for any of the API scopes "{}"'.format(api_scopes)
            )

    def validate_session(self):
        if OIDCBackChannelLogoutEvent.objects.is_session_terminated_for_token(self):
            raise ValidationError("Session has been terminated.")

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
        return get_scopes_from_claims(
            self.settings.API_AUTHORIZATION_FIELD, self.claims
        )
