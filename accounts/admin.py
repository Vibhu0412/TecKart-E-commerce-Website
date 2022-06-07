from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account, UserProfile


# Register your models here.
class AccountAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'date_joined', 'last_login', 'is_active')
    list_display_links = ('first_name', 'last_name', 'email')
    readonly_fields = ('date_joined', 'last_login')
    ordering = ('-date_joined',)

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()


class UserProfileAdmin(admin.ModelAdmin):
    def thumbnail(self, object):
        return format_html('<img src="{}" width="30" style="border-radius:50%;">'.format(object.profile_picture.url))
    thumbnail.short_description = 'Profile Picture'
    list_display = ('thumbnail', 'user', 'city', 'state', 'country')


admin.site.register(Account, AccountAdmin)
admin.site.register(UserProfile, UserProfileAdmin)

# Changing Admin Header
admin.site.site_header = "VS E-Commerce Admin Panel"
