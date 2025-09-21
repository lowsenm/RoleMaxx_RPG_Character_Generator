from django import forms
from chargenapp.models import CharacterOption
import json
import os
from django.conf import settings


# Forms defines how users interact with your model in the frontend.

# Django form with checkboxes
class CharacterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        with open(os.path.join(settings.BASE_DIR, 'chargenapp/data/CharacterOptions.json')) as f:
            options = json.load(f)
        
        self.fields['race'].choices = [(opt, opt) for opt in options['Race']]
        self.fields['char_class'].choices = [(opt, opt) for opt in options['Class']]
        self.fields['background'].choices = [(opt, opt) for opt in options['Background']]
        self.fields['level'].choices = [(opt, opt) for opt in options['Level']]
        self.fields['alignment'].choices = [(opt, opt) for opt in options['Alignment']]
        self.fields['sex'].choices = [(opt, opt) for opt in options['Sex']]




    char_name = forms.CharField(max_length=100, required=False, label='Character Name')

    race = forms.ChoiceField(
        choices=[],
        widget=forms.RadioSelect,
        required=True,
        label='Select Race'
    )
    char_class = forms.ChoiceField(
        choices=[],
        widget=forms.RadioSelect,
        required=True,
        label='Select Class'
    )
    alignment = forms.ChoiceField(
        choices=[],
        widget=forms.RadioSelect,
        required=True,
        label='Select Alignment'
    )
    sex = forms.ChoiceField(
        choices=[],
        widget=forms.RadioSelect,
        required=True,
        label='This character is...'
    )
    background = forms.ChoiceField(
        choices=[],
        widget=forms.RadioSelect,
        required=True,
        label='Select Background'
    )

    LEVEL_CHOICES = [(str(i), str(i)) for i in range(1, 31)]

    level = forms.ChoiceField(
        choices=LEVEL_CHOICES,
        widget=forms.RadioSelect,
        label='Select Level'
    )

    player_name = forms.CharField(max_length=100, required=True, label='Player Name')
