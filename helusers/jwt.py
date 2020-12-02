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

    def validate(self, keys):
        """Verifies the JWT's signature using the provided keys,
        and validates the claims, raising an exception if anything fails."""
        self._claims = jwt.decode(self._encoded_jwt, keys)

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
