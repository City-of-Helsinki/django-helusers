try:
    from ._rest_framework_jwt_impl import (JWTAuthentication,
                                           get_user_id_from_payload_handler,
                                           patch_jwt_settings)
except ImportError:
    pass
