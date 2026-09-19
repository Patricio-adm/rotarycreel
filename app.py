from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Inicializar la aplicación Flask
app = Flask(__name__)
app.secret_key = 'clave_secreta_rotary_creel_2026'

# Configuración de la carpeta de subidas de fotos
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Asegurarse de que la carpeta de subidas exista
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
    
    # Manejar la subida del archivo de foto local asegurando formato de ruta limpio
    file = request.files.get('foto_archivo')
    if file and file.filename != '':
        if allowed_file(file.filename):
            filename = secure_filename(f"socio_{socio.id}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            # Guardamos la ruta relativa limpia empezando con /static/...
            socio.foto_url = f"/{filepath}" if not filepath.startswith('/') else filepath
    
    # Manejar puesto actual o nuevo cargo si se envía
    nuevo_cargo = request.form.get('cargo_actual')
    periodo_actual = request.form.get('periodo_actual', '2026-2027')
    
    if nuevo_cargo:
        for c in socio.cargos:
            if c.es_actual:
                c.es_actual = False
        
        cargo_db = HistorialCargo(socio_id=socio.id, cargo=nuevo_cargo, periodo=periodo_actual, es_actual=True)
        db.session.add(cargo_db)
        
    db.session.commit()
    flash('Socio y fotografía actualizados correctamente', 'success')
    return redirect(url_for('gestion_socios'))

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
