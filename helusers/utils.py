import base64
from uuid import UUID


def uuid_to_username(uuid):
    """
    Convert UUID to username.

    >>> uuid_to_username('00fbac99-0bab-5e66-8e84-2e567ea4d1f6')
    'u-ad52zgilvnpgnduefzlh5jgr6y'

    >>> uuid_to_username(UUID('00fbac99-0bab-5e66-8e84-2e567ea4d1f6'))
    'u-ad52zgilvnpgnduefzlh5jgr6y'
    """
    uuid_data = getattr(uuid, "bytes", None) or UUID(uuid).bytes
    b32coded = base64.b32encode(uuid_data)
    return "u-" + b32coded.decode("ascii").replace("=", "").lower()


def username_to_uuid(username):
    """
    Convert username to UUID.

    >>> username_to_uuid('u-ad52zgilvnpgnduefzlh5jgr6y')
    UUID('00fbac99-0bab-5e66-8e84-2e567ea4d1f6')
    """
    if not username.startswith("u-") or len(username) != 28:
        raise ValueError("Not an UUID based username: %r" % (username,))
    decoded = base64.b32decode(username[2:].upper() + "======")
    return UUID(bytes=decoded)


def get_nested_from_dict(data, full_key):
    """Get value from a nested dictionary with dot notation

    e.g.
    >>> get_nested_from_dict({"level1": {"level2": "value"}}, "level1")
    {'level2': 'value'}
    >>> get_nested_from_dict({"level1": {"level2": "value"}}, "level1.level2")
    'value'
    >>> get_nested_from_dict({"level1": [{"level2": "value1"}, {"level2": "value2"}]}, "level1.level2")
    ['value1', 'value2']
    """
    if not isinstance(data, dict) or not isinstance(full_key, str):
        return None

    key_parts = full_key.split(".")
    first_part = key_parts.pop(0)

    value = data.get(first_part, None)

    if len(key_parts) == 0:
        return value

    new_key = ".".join(key_parts)
    if isinstance(value, list):
        return [get_nested_from_dict(val, new_key) for val in value]

    return get_nested_from_dict(value, new_key)


def flatten_list(x):
    if isinstance(x, list):
        return [a for i in x for a in flatten_list(i)]
    else:
        return [x]


def is_list_of_non_empty_strings(value):
    return isinstance(value, list) and all(isinstance(x, str) and x for x in value)


def get_scopes_from_claims(authorization_fields, claims):
    if not authorization_fields or not claims:
        return None

    if isinstance(authorization_fields, str):
        authorization_fields = [authorization_fields]

    collected_api_scopes = []
    for authorization_field in authorization_fields:
        api_scopes = claims.get(authorization_field)
        if api_scopes is None and "." in authorization_field:
            api_scopes = flatten_list(get_nested_from_dict(claims, authorization_field))
            api_scopes = list(filter(None, api_scopes))
        collected_api_scopes.extend(api_scopes)

    if not is_list_of_non_empty_strings(collected_api_scopes):
        return None

    return set(collected_api_scopes)
