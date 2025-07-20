
from django.contrib import admin
from django.urls import path, include
from .views import home_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('session/', include('apps.core.urls')),
    path('accounts/', include('allauth.urls')),
    path('activities/', include('apps.activities.urls')),
    path('users/', include('apps.users.urls')),
    path('', home_view, name='home'),
]
