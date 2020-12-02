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

    @property
    def claims(self):
        """Returns all the claims of the JWT as a dictionary."""
        return jwt.get_unverified_claims(self._encoded_jwt)
