from .utils import get_scopes_from_claims

try:
    from ._rest_framework_jwt_impl import (  # noqa: F401
        JWTAuthentication,
        get_user_id_from_payload_handler,
        patch_jwt_settings,
    )
except ImportError:
    pass

import base64
import json as _json
import logging

import jwt as pyjwt
from django.utils.functional import cached_property
from jwt import PyJWK

from .models import OIDCBackChannelLogoutEvent
from .settings import api_token_auth_settings

logger = logging.getLogger(__name__)

_NOT_PROVIDED = object()


def _get_unverified_payload(encoded_jwt):
    """Base64-decode the JWT payload without touching the signature.

    Intentionally skips signature verification — callers must call
    JWT.validate() before trusting any claim values.
    """
    try:
        if isinstance(encoded_jwt, bytes):
            encoded_jwt = encoded_jwt.decode("utf-8")
        parts = encoded_jwt.split(".")
        if len(parts) != 3:
            raise pyjwt.exceptions.DecodeError("Not enough segments")
        # JWT compact serialisation strips base64 padding; restore it.
        padded = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = _json.loads(base64.urlsafe_b64decode(padded))
    except pyjwt.exceptions.DecodeError:
        raise
    except Exception as exc:
        raise pyjwt.exceptions.DecodeError("Invalid JWT payload") from exc
    if not isinstance(payload, dict):
        raise pyjwt.exceptions.DecodeError("Invalid JWT payload: not a JSON object")
    return payload


def _decode_jwt_with_keys(token, jwks, algorithms, options):
    """Decode a JWT by trying each key in the JWKS until one succeeds.

    Entries that cannot be constructed into usable key objects (unsupported
    kty, malformed key material, encryption-only keys, etc.) are skipped.
    Terminal failures — expired token, missing claims, algorithm mismatch —
    are raised immediately once a key has been successfully constructed.
    """
    key_list = jwks.get("keys", []) if isinstance(jwks, dict) else []
    if not key_list:
        raise pyjwt.exceptions.DecodeError("No keys available for validation")

    last_exc = None
    for jwk_data in key_list:
        try:
            key_obj = PyJWK(jwk_data)
        except Exception as exc:
            kid = (
                jwk_data.get("kid", "<no kid>")
                if isinstance(jwk_data, dict)
                else "<unknown>"
            )
            logger.debug("Skipping unusable JWK entry (kid=%s): %s", kid, exc)
            continue

        try:
            return pyjwt.decode(
                token, key_obj.key, algorithms=algorithms, options=options
            )
        except (
            pyjwt.exceptions.InvalidSignatureError,
            pyjwt.exceptions.InvalidKeyError,
            TypeError,
        ) as exc:
            # Wrong key or incompatible key type — try the next one
            last_exc = exc

    raise last_exc or pyjwt.exceptions.InvalidSignatureError("JWT validation failed")


class ValidationError(Exception):
    pass


class JWT:
    def __init__(self, encoded_jwt, settings=None):
        """The constructor checks that a JWT can be extracted from the
        provided input but it doesn't validate it in any way. If the
        input is invalid, an exception is raised."""
        self._encoded_jwt = encoded_jwt
        self._claims = _get_unverified_payload(encoded_jwt)
        self.settings = settings or api_token_auth_settings

    def validate(self, keys, audience, required_claims=_NOT_PROVIDED):
        """Verifies the JWT's signature using the provided keys,
        and validates the claims, raising an exception if anything fails.
        Required claims can be specified using the required_claims argument
        and it defaults to ["aud", "exp"]."""

        if required_claims is _NOT_PROVIDED:
            required_claims = ["aud", "exp"]

        require_aud = "aud" in required_claims
        remaining_claims = [c for c in required_claims if c != "aud"]

        options = {
            "verify_aud": False,
            "require": remaining_claims,
        }

        _decode_jwt_with_keys(
            self._encoded_jwt,
            keys,
            algorithms=self.settings.ALLOWED_ALGORITHMS,
            options=options,
        )

        claims = self.claims
        if require_aud and "aud" not in claims:
            raise ValidationError("Missing required 'aud' claim.")

        if "aud" in claims:
            claim_audiences = claims["aud"]
            if isinstance(claim_audiences, str):
                claim_audiences = {claim_audiences}
            elif isinstance(claim_audiences, list) and all(
                isinstance(a, str) for a in claim_audiences
            ):
                claim_audiences = set(claim_audiences)
            else:
                raise ValidationError("Invalid audience.")
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
            raise ValidationError(f"Unknown JWT issuer {issuer}.")

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
                f'Not authorized for any of the API scopes "{api_scopes}"'
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
