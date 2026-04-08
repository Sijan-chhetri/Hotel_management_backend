# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# from django.utils.translation import gettext_lazy as _
# from .models import User

# @admin.register(User)
# class UserAdmin(BaseUserAdmin):
#     ordering = ['id']
#     list_display = ['email', 'hotel_name', 'phone_number', 'is_staff']
#     search_fields = ['email', 'hotel_name']
    
#     fieldsets = (
#         (None, {'fields': ('email', 'password')}),
#         (_('Personal Info'), {'fields': ('hotel_name', 'address', 'city', 'state', 'country', 'zipcode', 'phone_number', 'description')}),
#         (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
#         (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
#     )

#     add_fieldsets = (
#         (None, {
#             'classes': ('wide',),
#             'fields': ('email', 'hotel_name', 'password1', 'password2', 'phone_number', 'address', 'city', 'state', 'country', 'zipcode', 'description'),
#         }),
#     )

#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = ['hotel_name']
    
