import datetime

from django.contrib.sessions.serializers import JSONSerializer
from django.utils.dateparse import parse_datetime


class TunnistamoOIDCSerializer(JSONSerializer):
    """Serializer capable of serializing session data with a datetime object.

    Datetime handling is required for TunnistamoOIDCAuth backend when using
    the `helusers.defaults.SOCIAL_AUTH_PIPELINE`.
    """

    datetime_field = "access_token_expires_at"

    def dumps(self, obj):
        if field := obj.get(self.datetime_field):
            if isinstance(field, datetime.datetime):
                obj[self.datetime_field] = field.isoformat()
        return super().dumps(obj)

    def loads(self, data):
        session = super().loads(data)
        if field := session.get(self.datetime_field):
            session[self.datetime_field] = parse_datetime(field)
        return session
