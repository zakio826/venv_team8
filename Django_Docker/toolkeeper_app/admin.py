from django.contrib import admin

from .models import Group, GroupMember, Asset, Item, Image, History, Result


admin.site.register(Group)
admin.site.register(GroupMember)
admin.site.register(Asset)
admin.site.register(Item)
admin.site.register(Image)
admin.site.register(History)
admin.site.register(Result)