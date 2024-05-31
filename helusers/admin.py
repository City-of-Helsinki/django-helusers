from django.conf import settings
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import ADGroup, ADGroupMapping, OIDCBackChannelLogoutEvent


@admin.register(ADGroupMapping)
class ADGroupMappingAdmin(admin.ModelAdmin):
    list_display = [
        "get_str",
        "get_ad_group_name",
        "get_ad_group_display_name",
        "group",
    ]
    list_filter = ("group",)
    search_fields = (
        "group__name",
        "ad_group__name",
        "ad_group__display_name",
    )

    ordering = ("ad_group__display_name", "group")

    @admin.display(description=_("Mapping"))
    def get_str(self, obj):
        return str(obj)

    @admin.display(description=_("AD group name"), ordering="ad_group__name")
    def get_ad_group_name(self, obj):
        return obj.ad_group.name

    @admin.display(
        description=_("AD group display name"), ordering="ad_group__display_name"
    )
    def get_ad_group_display_name(self, obj):
        return obj.ad_group.display_name


@admin.register(ADGroup)
class ADGroupAdmin(admin.ModelAdmin):
    list_display = [
        "display_name",
        "name",
    ]
    search_fields = (
        "display_name",
        "name",
    )
    ordering = ("display_name", "name")


if getattr(settings, "HELUSERS_BACK_CHANNEL_LOGOUT_ENABLED", False):

    @admin.register(OIDCBackChannelLogoutEvent)
    class OIDCBackChannelLogoutEventAdmin(admin.ModelAdmin):
        list_display = ["iss", "sub", "sid", "created_at"]
        readonly_fields = ["created_at"]
        search_fields = ["iss", "sub", "sid"]
