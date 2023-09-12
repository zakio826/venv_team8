from django.contrib import admin

from .models import Group, Asset, Item, Image, History, Result


admin.site.register(Group, Asset, Item, Image, History, Result)