from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
import base64
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Inicializar la aplicación Flask
app = Flask(__name__)
app.secret_key = 'clave_secreta_rotary_creel_2026'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

class Hijo(db.Model):
    __tablename__ = 'hijos'
    id = db.Column(db.Integer, primary_key=True)
    socio_id = db.Column(db.Integer, db.ForeignKey('socios.id'), nullable=False)
    nombre = db.Column(db.String(150), nullable=False)
    fecha_nacimiento = db.Column(db.Date)

class HistorialCargo(db.Model):
    __tablename__ = 'historial_cargos'
    id = db.Column(db.Integer, primary_key=True)
    socio_id = db.Column(db.Integer, db.ForeignKey('socios.id'), nullable=False)
    cargo = db.Column(db.String(100), nullable=False)
    periodo = db.Column(db.String(50), nullable=False)
    es_actual = db.Column(db.Boolean, default=False)

class Socio(db.Model):
    __tablename__ = 'socios'
    id = db.Column(db.Integer, primary_key=True)
    numero_socio = db.Column(db.String(50))
    nombre_completo = db.Column(db.String(150), nullable=False)
    telefono = db.Column(db.String(50))
    correo = db.Column(db.String(100))
    fecha_nacimiento = db.Column(db.Date)
    es_activo = db.Column(db.Boolean)
    tipo_socio = db.Column(db.String(50))
    calle_numero = db.Column(db.String(150))
    colonia = db.Column(db.String(100))
    codigo_postal = db.Column(db.String(20))
    ciudad = db.Column(db.String(100))
    estado = db.Column(db.String(100))
    estado_civil = db.Column(db.String(50))
    
    # Datos familiares
    nombre_esposa = db.Column(db.String(150))
    fecha_nacimiento_esposa = db.Column(db.Date)
    aniversario_matrimonio = db.Column(db.Date)
    telefono_esposa = db.Column(db.String(50))
    telefono_emergencia = db.Column(db.String(50))
    foto_url = db.Column(db.Text)  # Almacena Base64
    
    # Relaciones
    cargos = db.relationship('HistorialCargo', backref='socio', lazy=True, cascade="all, delete-orphan")
    hijos = db.relationship('Hijo', backref='socio', lazy=True, cascade="all, delete-orphan")

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

# 1. Página de Inicio Pública
@app.route('/')
def index_publico():
    lista_socios = Socio.query.all()
    return render_template('publico.html', socios=lista_socios)

# 2. Inicio de Sesión para Administración
@app.route('/login', methods=['GET', 'POST'])
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
    
    lista_socios = Socio.query.all()
    return render_template('socios.html', socios=lista_socios)

@app.route('/socios/editar/<int:id>', methods=['POST'])
def editar_socio(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    socio = Socio.query.get_or_404(id)
    socio.nombre_completo = request.form.get('nombre_completo')
    socio.telefono = request.form.get('telefono')
    socio.correo = request.form.get('correo')
    socio.tipo_socio = request.form.get('tipo_socio')
    socio.ciudad = request.form.get('ciudad')
    
    # Datos familiares
    socio.nombre_esposa = request.form.get('nombre_esposa')
    socio.telefono_esposa = request.form.get('telefono_esposa')
    socio.telefono_emergencia = request.form.get('telefono_emergencia')
    
    def parse_date(date_str):
        if date_str:
            try:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return None
        return None

    socio.fecha_nacimiento_esposa = parse_date(request.form.get('fecha_nacimiento_esposa'))
    socio.aniversario_matrimonio = parse_date(request.form.get('aniversario_matrimonio'))
    
    # Manejar subida segura de foto en Base64
    try:
        file = request.files.get('foto_archivo')
        if file and file.filename != '':
            if allowed_file(file.filename):
                file_bytes = file.read()
                if file_bytes:
                    encoded_img = base64.b64encode(file_bytes).decode('utf-8')
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    mime_type = "image/jpeg" if ext in ['jpg', 'jpeg'] else f"image/{ext}"
                    socio.foto_url = f"data:{mime_type};base64,{encoded_img}"
    except Exception as e:
        print(f"Error procesando imagen: {e}")

    # Agregar nuevo cargo (histórico o actual)
    nuevo_cargo = request.form.get('cargo_nuevo')
    periodo_nuevo = request.form.get('periodo_nuevo')
    es_actual = request.form.get('es_actual') == 'on'
    
    if nuevo_cargo and periodo_nuevo:
        if es_actual:
            for c in socio.cargos:
                c.es_actual = False
                
        cargo_db = HistorialCargo(
            socio_id=socio.id, 
            cargo=nuevo_cargo, 
            periodo=periodo_nuevo, 
            es_actual=es_actual
        )
        db.session.add(cargo_db)
        
    db.session.commit()
    flash('Información del socio, familia y cargos actualizados correctamente', 'success')
    return redirect(url_for('gestion_socios'))

@app.route('/tesoreria')
def modulo_tesoreria():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('tesoreria.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index_publico'))

if __name__ == '__main__':
    app.run(debug=True)
