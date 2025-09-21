from django.shortcuts import render
from django.http import FileResponse
#import subprocess
#import json
#import os
from django.conf import settings
from .forms import CharacterForm  # Make sure this import exists and is correct
from django.core.serializers import serialize
from django.http import JsonResponse
from .chargen import chargen_call

# Views handles logic when the user loads the form or submits it.
# character_dict turned into plain dictionary and sent to chargen.py

#def serialize(data):
#    queryset = data.objects.all()
#    serialized_data = serialize("json", queryset)
#    # If you need to manipulate the data as a Python object before sending
#    python_data = json.loads(serialized_data)
#    return JsonResponse(python_data, safe=False) # safe=False is needed if the top-level object is not a dict

from django.http import HttpResponse


def character_form(request):
    if request.method == "POST":

    # POST request contains user slections
        form = CharacterForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            # Convert all model fields to plain strings
            character_data = {
                "CharacterName": str(data["char_name"]),
                "CharacterNameA": str(data["char_name"]),
                "Race": str(data["race"]),
                "Class": str(data["char_class"]),
                "Background": str(data["background"]),
                "Level": str(data["level"]),
                "Alignment": str(data["alignment"]),
                "Sex": str(data["sex"]),
                "PlayerName": str(data["player_name"]),
            }

    # Write to JSON
    #            file_path = os.path.join(settings.BASE_DIR, "chargenapp", "data", "user_inputs.json")
    #            with open(file_path, "w", encoding="utf-8") as f:
    #                json.dump(character_data, f)

    # Call chargen.py
    #            chargen_path = os.path.join(settings.BASE_DIR, "chargenapp", "chargen.py")

    # Return generated PDF
            pdf_path = chargen_call(character_data)
            return FileResponse(open(pdf_path, "rb"), content_type="application/pdf")

    else:
        form = CharacterForm()

    # GET request renders the blank form
    return render(request, "chargenapp/chargen_form.html", {"form": form})
