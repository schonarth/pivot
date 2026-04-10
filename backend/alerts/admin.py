from django.contrib import admin
from .models import Alert, AlertTrigger

admin.site.register(Alert)
admin.site.register(AlertTrigger)