from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
import firebase_admin
from firebase_admin import credentials, db
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import json

# Inicialización de Firebase
# Leer el JSON de la variable de entorno 'GOOGLE_APPLICATION_CREDENTIALS_JSON'
firebase_creds = json.loads(os.getenv("config/GOOGLE_APPLICATION_CREDENTIALS_JSON"))

# Configurar las credenciales con el diccionario JSON
cred = credentials.Certificate(firebase_creds)
firebase_admin.initialize_app(cred, {
    'storageBucket': os.getenv("laura-24a17.appspot.com"),
    'databaseURL': os.getenv("https://laura-24a17-default-rtdb.firebaseio.com")
})

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
CITY = 'Arequipa'

class User(UserMixin):
    """Clase User que representa a los usuarios autenticados."""
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

def obtener_temperatura_real():
    """Obtiene la temperatura real desde OpenWeatherMap."""
    url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        temperatura = data['main']['temp']
        return temperatura
    else:
        print(f"Error al obtener la temperatura: {response.status_code} - {response.text}")
        return None

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/fotos')
@login_required
def obtener_fotos():
    """Devuelve las fotos más recientes en formato JSON."""
    ref = db.reference('detecciones')
    detecciones = ref.get()

    fotos = []
    if detecciones:
        for key, value in detecciones.items():
            fotos.append({
                'url': value['url_foto'], 
                'fecha_hora': value['fecha_hora'], 
                'temperatura': value.get('temperatura', 'N/A')
            })

    return jsonify(fotos=fotos)

@app.route('/temperatura')
@login_required
def obtener_temperatura():
    """Devuelve la temperatura real."""
    temperatura = obtener_temperatura_real()
    if temperatura is not None:
        return jsonify(temperatura=temperatura)
    else:
        return jsonify(error='Error al obtener la temperatura'), 500

# Rutas de autenticación
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        ref = db.reference('users')
        user_data = ref.order_by_child('email').equal_to(email).get()

        if user_data:
            flash('El usuario ya existe. Intente iniciar sesión.')
        else:
            ref.push({'email': email, 'password': hashed_password})
            flash('Usuario registrado exitosamente. Ahora puede iniciar sesión.')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        ref = db.reference('users')
        user_data = ref.order_by_child('email').equal_to(email).get()

        if user_data:
            for key, value in user_data.items():
                if check_password_hash(value['password'], password):
                    user = User(id=key)
                    login_user(user)
                    return redirect(url_for('index'))
                else:
                    flash('Contraseña incorrecta. Intente de nuevo.')
        else:
            flash('Usuario no encontrado. Regístrese primero.')

    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
