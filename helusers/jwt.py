try:
    from ._rest_framework_jwt_impl import (JWTAuthentication,
                                           get_user_id_from_payload_handler,
                                           patch_jwt_settings)
except ImportError:
    pass

from jose import jwt


class JWT:
    def __init__(self, encoded_jwt):
        self._encoded_jwt = encoded_jwt

    def validate(self, keys, audience):
        """Verifies the JWT's signature using the provided keys,
        and validates the claims, raising an exception if anything fails."""

        options = {
            "require_aud": True,
        }

        self._claims = jwt.decode(
            self._encoded_jwt, keys, options=options, audience=audience
        )

    @property
    def issuer(self):
        """Returns the "iss" claim value."""
        return self.claims["iss"]

    @property
    def claims(self):
        """Returns all the claims of the JWT as a dictionary."""
        if not hasattr(self, "_claims"):
            self._claims = jwt.get_unverified_claims(self._encoded_jwt)
        return self._claims
