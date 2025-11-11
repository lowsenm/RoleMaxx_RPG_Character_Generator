"# RPG-Create-a-Character" 
"# a user-filled webpage form that returns a fleshed-out RPG character sheet."

"## To push changes:"
1. "STAGE AND RECORD CHANGES
git add .
git commit -m "Describe your changes"
"

2. "PUSH TO GITHUB
git push origin main
"

3. "PULL TO PYTHONANYWHERE
cd ~/RPG_Character_Generator  # or wherever your site lives
(use this console: https://www.pythonanywhere.com/user/lowsenm/consoles/)
git pull origin main (enter github username / token)
"
4. "RELOAD ON PYTHONANYWHERE
Hit RELOAD here: https://www.pythonanywhere.com/user/lowsenm/webapps/#tab_id_www_lowsen_com
Then goto site
"

5. "VIRTUAL ENVIRONMENT: C:\Users\lowse\Documents\Games\CharGen\older versions\.venv\Scripts
activate"

"Or all together, on pushing system:
cd C:\Users\lowse\Documents\Games\CharGen\chargen3pa
git add .
git commit -m "testing spellcast"
git push origin main

On the pulling system:
git pull origin main
"

6. "For the dev environment, use the following settings:
"chargenproj/settings.py - dev settings at bottom; quote out for prod
chargenapp/chargen.py - switch # GENERATE BACKGROUND and # GENERATE PIC
TO CHECK if browser demands HTTPS: Chrome/Settings/Privacy & Security: delete cookies and cache

In CLI:
cd C:\Users\lowse\Documents\Games\CharGen\older versions\.venv\Scripts
activate
cd C:\Users\lowse\Documents\Games\CharGen\chargen3pa
python manage.py runserver

The .venv site:
http://127.0.0.1:8000/
"