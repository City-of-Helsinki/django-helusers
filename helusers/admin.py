from .models import ADGroupMapping
from django.contrib import admin


@admin.register(ADGroupMapping)
class ADGroupMappingAdmin(admin.ModelAdmin):
    pass
