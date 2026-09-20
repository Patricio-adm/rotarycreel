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

def to_upper(val):
    return val.strip().upper() if val else None

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

class AutoridadRotaria(db.Model):
    __tablename__ = 'autoridades_rotarias'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    cargo = db.Column(db.String(150), nullable=False)
    nivel = db.Column(db.String(50), nullable=False)  # 'Internacional' o 'Distrital'
    correo = db.Column(db.String(100))
    telefono = db.Column(db.String(50))

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
    foto_url = db.Column(db.Text)
    
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

@app.route('/')
def index_publico():
    lista_socios = Socio.query.all()
    return render_template('publico.html', socios=lista_socios)

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
    socio.nombre_completo = to_upper(request.form.get('nombre_completo'))
    socio.telefono = to_upper(request.form.get('telefono'))
    socio.correo = request.form.get('correo') # El correo se respeta en minúsculas/normal
    socio.tipo_socio = to_upper(request.form.get('tipo_socio'))
    socio.ciudad = to_upper(request.form.get('ciudad'))
    
    socio.nombre_esposa = to_upper(request.form.get('nombre_esposa'))
    socio.telefono_esposa = to_upper(request.form.get('telefono_esposa'))
    socio.telefono_emergencia = to_upper(request.form.get('telefono_emergencia'))
    
    def parse_date(date_str):
        if date_str:
            try:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return None
        return None

    socio.fecha_nacimiento_esposa = parse_date(request.form.get('fecha_nacimiento_esposa'))
    socio.aniversario_matrimonio = parse_date(request.form.get('aniversario_matrimonio'))
    
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

    nuevo_cargo = request.form.get('cargo_nuevo')
    periodo_nuevo = request.form.get('periodo_nuevo')
    es_actual = request.form.get('es_actual') == 'on'
    
    if nuevo_cargo and periodo_nuevo:
        if es_actual:
            for c in socio.cargos:
                c.es_actual = False
                
        cargo_db = HistorialCargo(
            socio_id=socio.id, 
            cargo=to_upper(nuevo_cargo), 
            periodo=to_upper(periodo_nuevo), 
            es_actual=es_actual
        )
        db.session.add(cargo_db)
        
    db.session.commit()
    flash('Información del socio, familia y cargos actualizados correctamente', 'success')
    return redirect(url_for('gestion_socios'))

@app.route('/cumpleanos-mes')
def cumpleanos_mes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    mes_actual = datetime.now().month
    todos_socios = Socio.query.all()
    festividades = []
    
    for socio in todos_socios:
        if socio.fecha_nacimiento and socio.fecha_nacimiento.month == mes_actual:
            festividades.append({
                'dia': socio.fecha_nacimiento.day,
                'fecha_str': socio.fecha_nacimiento.strftime('%d/%m/%Y'),
                'tipo': 'CUMPLEANOS SOCIO',
                'persona': socio.nombre_completo,
                'detalle': f"SOCIO ID: {socio.numero_socio or socio.id}"
            })
        
        if socio.fecha_nacimiento_esposa and socio.fecha_nacimiento_esposa.month == mes_actual:
            festividades.append({
                'dia': socio.fecha_nacimiento_esposa.day,
                'fecha_str': socio.fecha_nacimiento_esposa.strftime('%d/%m/%Y'),
                'tipo': 'CUMPLEANOS ESPOSA(O)',
                'persona': socio.nombre_esposa or 'ESPOSA(O)',
                'detalle': f"ESPOSA DE: {socio.nombre_completo}"
            })
                
        if socio.aniversario_matrimonio and socio.aniversario_matrimonio.month == mes_actual:
            festividades.append({
                'dia': socio.aniversario_matrimonio.day,
                'fecha_str': socio.aniversario_matrimonio.strftime('%d/%m/%Y'),
                'tipo': 'ANIVERSARIO DE BODAS',
                'persona': f"{socio.nombre_completo} Y {socio.nombre_esposa or 'CÓNYUGE'}",
                'detalle': "ANIVERSARIO MATRIMONIAL"
            })
                
        if socio.hijos:
            for hijo in socio.hijos:
                if hijo.fecha_nacimiento and hijo.fecha_nacimiento.month == mes_actual:
                    festividades.append({
                        'dia': hijo.fecha_nacimiento.day,
                        'fecha_str': hijo.fecha_nacimiento.strftime('%d/%m/%Y'),
                        'tipo': 'CUMPLEANOS HIJO(A)',
                        'persona': hijo.nombre,
                        'detalle': f"HIJO(A) DE: {socio.nombre_completo}"
                    })

    festividades = sorted(festividades, key=lambda x: x['dia'])
    nombre_mes_actual = datetime.now().strftime('%B').upper()
    return render_template('cumpleanos.html', festividades=festividades, mes_actual=nombre_mes_actual)

@app.route('/autoridades')
def gestion_autoridades():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    autoridades = AutoridadRotaria.query.all()
    return render_template('autoridades.html', autoridades=autoridades)

@app.route('/autoridades/guardar', methods=['POST'])
def guardar_autoridad():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    auth_id = request.form.get('auth_id')
    nombre = to_upper(request.form.get('nombre'))
    cargo = to_upper(request.form.get('cargo'))
    nivel = to_upper(request.form.get('nivel'))
    correo = request.form.get('correo')
    telefono = to_upper(request.form.get('telefono'))
    
    if auth_id:
        autoridad = AutoridadRotaria.query.get_or_404(auth_id)
        autoridad.nombre = nombre
        autoridad.cargo = cargo
        autoridad.nivel = nivel
        autoridad.correo = correo
        autoridad.telefono = telefono
        flash('Autoridad rotaria actualizada correctamente', 'success')
    else:
        nueva = AutoridadRotaria(nombre=nombre, cargo=cargo, nivel=nivel, correo=correo, telefono=telefono)
        db.session.add(nueva)
        flash('Autoridad rotaria agregada correctamente', 'success')
        
    db.session.commit()
    return redirect(url_for('gestion_autoridades'))

@app.route('/autoridades/eliminar/<int:id>')
def eliminar_autoridad(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    autoridad = AutoridadRotaria.query.get_or_404(id)
    db.session.delete(autoridad)
    db.session.commit()
    flash('Autoridad eliminada correctamente', 'success')
    return redirect(url_for('gestion_autoridades'))

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
