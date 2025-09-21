from django.db import models

# Models defines the database structure, storing selectable options for the form 
# (e.g., Races, Classes) to populate the form fields dynamically.

# Django model for character options - I believe it pulls these from db.sqlite3
class CharacterOption(models.Model):
    CATEGORY_CHOICES = [
        ('Character Name', 'Character Name'),
        ('Race', 'Race'),
        ('Class', 'Class'),
        ('Background', 'Background'),
        ('Alignment', "Alignment"),
        ("Level", "Level"),
        ("Sex", "Sex"),
        ("Player Name", "Player Name")
    ]

    # defines categories and names (of cats)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES) # Race, Class, etc.
    name = models.CharField(max_length=100) # Elf, Wizard, etc.

    def __str__(self):
        return self.name  # This makes checkboxes display names instead of "CharacterOption object (1)"


class Ability(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    default_score = models.IntegerField(default=10)

    def __str__(self):
        return f"{self.name} ({self.default_score})"


class SpecStats(models.Model):
    name = models.CharField(max_length=50, unique=True)
    abilities = models.ManyToManyField('Ability', blank=True)

    def __str__(self):
        return self.name

# The following seeds sqlite, but won't do so unless you force it to do so in shell within command prompt
# provides subcats (name=) within each of the categories - may need to run seed_database() in powershell
#def seed_database():
#    if not CharacterOption.objects.exists():
#        options = [
#            CharacterOption(category='Race', name='Elf'),
#            CharacterOption(category='Race', name='Dwarf'),
#            CharacterOption(category='Race', name='Human'),
#            CharacterOption(category='Class', name='Fighter'),
#            CharacterOption(category='Class', name='Wizard'),
#            CharacterOption(category='Background', name='Noble'),
#            CharacterOption(category='Background', name='Soldier'),
#            CharacterOption(category='Background', name='Noble'),
#        ]
#        CharacterOption.objects.bulk_create(options) # populates the CharacterOption class w/options above
