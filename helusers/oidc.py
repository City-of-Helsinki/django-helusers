try:
    from ._oidc_auth_impl import ApiTokenAuthentication, resolve_user
except ImportError:
    pass
