from django.contrib import admin

from .forms import CustomUserCreationForm
from django.contrib.auth.admin import UserAdmin

from .models import User, week, elevators, service, Message


class CustomUserAdmin(UserAdmin):
    model = User

    fieldsets = (
        *UserAdmin.fieldsets,
        (
            'Stats',
            {
                'fields': (
                    'phone_number',
                    'address',
                    'region',
                    'profile_pic'

                )
            }
        )
    )


admin.site.register(User, CustomUserAdmin)
admin.site.register(week)
admin.site.register(elevators)
admin.site.register(service)
admin.site.register(Message)
