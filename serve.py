from waitress import serve
from chargenproj.wsgi import application

serve(application, listen='0.0.0.0:8000')

