from django.contrib import admin
from .models import CharacterOption

# places CharacterOption in /admin page to allow manipulation
admin.site.register(CharacterOption)