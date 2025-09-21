from django.core.management.base import BaseCommand
from chargenapp.models import CharacterOption

class Command(BaseCommand):
    help = 'Import race, class, and background options from a text file'

    def handle(self, *args, **kwargs):
        file_path = "character_options.txt"  # Ensure this file exists in your project root

        try:
            with open(file_path, "r") as file:
                for line in file:
                    line = line.strip()
                    if not line:
                        continue  # Skip empty lines
                    
                    category, name = line.split(",")  # Split by comma
                    category = category.strip()
                    name = name.strip()

                    # Avoid duplicates
                    if not CharacterOption.objects.filter(category=category, name=name).exists():
                        CharacterOption.objects.create(category=category, name=name)
                        self.stdout.write(self.style.SUCCESS(f"Added {category}: {name}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"Skipped duplicate: {category} - {name}"))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR("File not found. Please ensure character_options.txt exists."))
