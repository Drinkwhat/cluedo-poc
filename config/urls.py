"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from ninja import NinjaAPI

# Initialize Ninja API
api = NinjaAPI(
    title="Cluedo Tracker API",
    version="1.0.0",
    description="API per gestione carte Cluedo in rete locale",
    docs_url="/api/docs/",
)

# Import API routers
from cluedo_game.api import router as app_router

# Add routers to API
api.add_router("/", app_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
    path('', include('cluedo_game.urls')),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Django Debug Toolbar
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
