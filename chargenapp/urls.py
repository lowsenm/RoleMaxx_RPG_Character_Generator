from django.urls import path
from . import views
from django.contrib import admin
from chargenapp.views import character_form
from django.conf import settings
from django.conf.urls.static import static
import os

#urlpatterns = [
#    path('admin/', admin.site.urls), # URL=xxx/admin/; already in project - don't need it again in app
#    path('', index, name='index')
#    path("", views.index, name="index"), # app's open/base URL (""); maps to views/index, alt name 'index'
#] + static(settings.STATIC_URL, document_root=os.path.join(settings.BASE_DIR, "chargenapp", "static"))

# chargen 3.0 view
urlpatterns = [
    path("", character_form, name="character_form"),
]
