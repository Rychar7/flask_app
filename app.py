from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
import firebase_admin
from firebase_admin import credentials, db
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import json
from collections import defaultdict
from datetime import datetime

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

API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
CITY = 'Arequipa'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

def obtener_temperatura_real():
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
def home():
    return render_template('home.html')

@app.route('/fotos')
@login_required
def obtener_fotos():
    ref = db.reference('detecciones')
    detecciones = ref.get()

    # Agrupar fotos por mes
    fotos_por_mes = defaultdict(list)
    monthly_photo_counts = defaultdict(int)

    if detecciones:
        for key, value in detecciones.items():
            fecha_hora = value['fecha_hora']
            date_obj = datetime.strptime(fecha_hora, "%Y-%m-%d %H:%M:%S")
            mes = date_obj.strftime("%B %Y")  # Ejemplo: "Enero 2024"
            
            fotos_por_mes[mes].append({
                'url': value['url_foto'],
                'fecha_hora': fecha_hora,
                'temperatura': value.get('temperatura', 'N/A')
            })
            monthly_photo_counts[mes] += 1

    # Asegúrate de pasar las variables correctas al template
    return render_template('fotos.html', fotos_por_mes=fotos_por_mes, monthly_photo_counts=monthly_photo_counts, title="Fotos Capturadas")

@app.route('/temperatura')
@login_required
def obtener_temperatura():
    temperatura = obtener_temperatura_real()
    return render_template('temperatura.html', temperatura=temperatura)

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
