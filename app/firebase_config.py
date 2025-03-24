import json
import os
import firebase_admin
from firebase_admin import credentials, storage
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Leer las credenciales de Firebase desde el .env (la variable debe contener un JSON válido)
firebase_credentials = json.loads(os.getenv("FIREBASE_CREDENTIALS"))
storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET")

# Inicializar Firebase Admin si no está ya inicializado
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_credentials)
    firebase_admin.initialize_app(cred, {
        "storageBucket": storage_bucket
    })

# Obtener el bucket de Firebase Storage
bucket = storage.bucket()
