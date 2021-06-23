from django.conf import settings
from django.contrib import admin

from .models import ADGroupMapping, ADGroup, OIDCBackChannelLogoutEvent


@admin.register(ADGroupMapping)
class ADGroupMappingAdmin(admin.ModelAdmin):
    pass

admin.site.register(ADGroup)


if getattr(settings, "HELUSERS_BACK_CHANNEL_LOGOUT_ENABLED", False):
    @admin.register(OIDCBackChannelLogoutEvent)
    class OIDCBackChannelLogoutEventAdmin(admin.ModelAdmin):
        list_display = ["iss", "sub", "sid", "created_at"]
        readonly_fields = ["created_at"]
        search_fields = ["iss", "sub", "sid"]
