from django.apps import AppConfig
import os


class CharacterCreatorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'character_creator'

    def ready(self): # ready causes run on startup
        """Runs on Django startup"""
        if os.environ.get('RUN_MAIN') == 'true':  # Prevents double execution in dev mode
            from chargenapp.management.commands.import_character_options import Command
            Command().handle()  # Runs the import script
            

# initializez ChargenappConfig class
class ChargenappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chargenapp'

