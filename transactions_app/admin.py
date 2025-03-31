from django.contrib import admin
from .models import *
from unfold.admin import ModelAdmin as UnflodModelAdmin

# Register your models here.
admin.site.register(NatureGroup,UnflodModelAdmin)
admin.site.register(MainGroup,UnflodModelAdmin)
admin.site.register(Ledger,UnflodModelAdmin)
admin.site.register(Transaction,UnflodModelAdmin)
admin.site.register(ShareUsers,UnflodModelAdmin)
admin.site.register(ProfitLossShareTransaction,UnflodModelAdmin)
admin.site.register(ShareUserTransaction,UnflodModelAdmin)
admin.site.register(CashCountSheet,UnflodModelAdmin)