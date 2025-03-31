from django.contrib import admin
from unfold.admin import ModelAdmin as UnflodModelAdmin
from .models import DeliveryDriver, DeliveryOrder

admin.site.register(DeliveryDriver, UnflodModelAdmin)
admin.site.register(DeliveryOrder, UnflodModelAdmin)
