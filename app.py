from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.security import generate_password_hash, check_password_hash

# Inicializar la aplicación Flask
app = Flask(__name__)
app.secret_key = 'clave_secreta_rotary_creel_2026'

# Configuración de la base de datos (con tu conexión a Supabase)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://postgres.smbrfdwruccudlcjdabs:rotary4110creel@aws-0-ca-central-1.pooler.supabase.com:6543/postgres')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app, engine_options={
    "pool_pre_ping": True,
    "pool_recycle": 300,
})

# Modelos de la Base de Datos
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

class Socio(db.Model):
    __tablename__ = 'socios'
    id = db.Column(db.Integer, primary_key=True)
    numero_socio = db.Column(db.String(50))
    nombre_completo = db.Column(db.String(150), nullable=False)
    telefono = db.Column(db.String(50))
    correo = db.Column(db.String(100))
    tipo_socio = db.Column(db.String(50))
    ciudad = db.Column(db.String(100))
    estado = db.Column(db.String(100))
    es_activo = db.Column(db.Boolean)
    foto_url = db.Column(db.String(255))
    
    # Relación con el historial de cargos
    cargos = db.relationship('HistorialCargo', backref='socio', lazy=True, cascade="all, delete-orphan")

class HistorialCargo(db.Model):
    __tablename__ = 'historial_cargos'
    id = db.Column(db.Integer, primary_key=True)
    socio_id = db.Column(db.Integer, db.ForeignKey('socios.id'), nullable=False)
    cargo = db.Column(db.String(100), nullable=False)
    periodo = db.Column(db.String(50), nullable=False)
    es_actual = db.Column(db.Boolean, default=False)

# Crear tablas automáticamente y asegurar usuario administrador al iniciar
with app.app_context():
    db.create_all()
    if not Usuario.query.filter_by(username='admin').first():
        admin_user = Usuario(
            username='admin',
            password_hash=generate_password_hash('rotary2026')
        )
        db.session.add(admin_user)
        db.session.commit()

# Rutas de la Aplicación

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = Usuario.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('menu_principal'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
            
    return render_template('login.html')

@app.route('/menu')
def menu_principal():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('menu.html')

@app.route('/socios')
def gestion_socios():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Consulta directa para verificar el padrón
    lista_socios = Socio.query.all()
    print(f"Socios encontrados en base de datos: {len(lista_socios)}")
        
    return render_template('socios.html', socios=lista_socios)

@app.route('/tesoreria')
def modulo_tesoreria():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('tesoreria.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
