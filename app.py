from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import json

# Inicialización de Firebase
firebase_creds_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if not firebase_creds_json:
    raise ValueError("La variable de entorno 'GOOGLE_APPLICATION_CREDENTIALS_JSON' no está configurada correctamente.")

firebase_creds = json.loads(firebase_creds_json)
cred = credentials.Certificate(firebase_creds)
firebase_admin.initialize_app(cred, {
    'storageBucket': 'laura-24a17.appspot.com',
    'databaseURL': 'https://laura-24a17-default-rtdb.firebaseio.com'
})

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/')
@login_required
def home():
    return render_template('home.html')

@app.route('/temperatura')
@login_required
def obtener_temperatura():
    # Obtener datos de la tabla "detecciones"
    ref_detecciones = db.reference('detecciones')
    detecciones = ref_detecciones.get()

    # Obtener datos de la tabla "temperatura"
    ref_temperatura = db.reference('temperatura')
    temperatura_db = ref_temperatura.get()

    temperaturas = []  # Lista combinada de temperaturas
    if detecciones:
        for key, value in detecciones.items():
            try:
                fecha_hora = datetime.strptime(value['fecha_hora'], "%Y%m%d_%H%M%S")
                temperaturas.append({
                    'fecha': fecha_hora.strftime("%Y-%m-%d"),
                    'hora': fecha_hora.strftime("%H:%M:%S"),
                    'temperatura': value.get('temperatura', 'N/A')
                })
            except ValueError:
                print(f"Error procesando fecha: {value['fecha_hora']}")
                continue

    if temperatura_db:
        for key, value in temperatura_db.items():
            try:
                fecha_hora = datetime.strptime(value['fecha_hora'], "%Y%m%d_%H%M%S")
                temperaturas.append({
                    'fecha': fecha_hora.strftime("%Y-%m-%d"),
                    'hora': fecha_hora.strftime("%H:%M:%S"),
                    'temperatura': value.get('temperatura', 'N/A')
                })
            except ValueError:
                print(f"Error procesando fecha: {value['fecha_hora']}")
                continue

    # Ordenar las temperaturas por fecha y hora
    temperaturas = sorted(temperaturas, key=lambda x: (x['fecha'], x['hora']))

    return render_template('temperatura.html', temperaturas=temperaturas)

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
                    return redirect(url_for('home'))
                else:
                    flash('Contraseña incorrecta. Intente de nuevo.')
        else:
            flash('Usuario no encontrado. Regístrese primero.')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
