"""
URL configuration for carbazzar_final project.
"""

from django.contrib import admin
from django.urls import path, include   # ✅ IMPORT THESE
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('api.urls')),      # ✅ include all app routes
    # path('admin/', admin.site.urls),  # optional — keep commented if not using Django admin
]

# ✅ To serve media files (e.g., uploaded car images) during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
