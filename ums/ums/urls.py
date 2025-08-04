
from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from .views import home_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('session/', include('apps.core.urls')),
    path('accounts/', include('allauth.urls')),
    path('activities/', include('apps.activities.urls')),
    path('users/', include('apps.users.urls')),
    path('academic/', include('apps.academic.urls')),
    path('', home_view, name='home'),
]   

if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls
    urlpatterns += debug_toolbar_urls()
