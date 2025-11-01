#  RLS Symptommonitoring – Backend  

Backend für ein System zur Erfassung und Analyse von Symptomen des Restless-Legs-Syndroms (RLS).  
Bereitstellung einer sicheren API zur Patient*innendatenerfassung, Authentifizierung und FHIR-kompatiblen Struktur.

---

##  Aktueller Stand

Django Projekt eingerichtet  ✅  
Conda-Umgebung eingerichtet  ✅  
User Registrierung & Login (JWT)  ✅ funktioniert  
API-Dokumentation (Swagger)  ✅ aktiviert  
Thunder Client Test  ✅ erfolgreich  

Das Backend läuft lokal und ist bereit für die Weiterentwicklung 

---

##  Setup-Anleitung 

### 1) Conda-Umgebung erstellen & aktivieren
conda create --name rls-backend python=3.11
conda activate rls-backend

2) Benötigte Pakete installieren
pip install django djangorestframework djangorestframework-simplejwt drf-spectacular fhir.resources

3) Server starten
python manage.py migrate
python manage.py runserver

4) Im Browser öffnen
Funktion + URL
Swagger API Docs http://127.0.0.1:8000/api/docs/

Registrierung	POST /api/accounts/register/
Login	POST /api/accounts/login/

Zum Testen Thunder Client (VS Code)
