from django.contrib import admin
from .models import CashTransaction, Portfolio, PortfolioSnapshot

admin.site.register(Portfolio)
admin.site.register(CashTransaction)
admin.site.register(PortfolioSnapshot)