from .models import ADGroupMapping, ADGroup
from django.contrib import admin


@admin.register(ADGroupMapping)
class ADGroupMappingAdmin(admin.ModelAdmin):
    pass

admin.site.register(ADGroup)
