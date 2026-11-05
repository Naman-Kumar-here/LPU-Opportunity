from django.contrib import admin
from .models import Profile, Opportunity , Application

# Register your models here.
admin.site.register(Profile)
admin.site.register(Opportunity)
admin.site.register(Application)