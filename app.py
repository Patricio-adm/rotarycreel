from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
import base64
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'clave_secreta_rotary_creel_2026')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def to_upper(val):
    if val and isinstance(val, str):
        cleaned = val.strip().upper()
        return cleaned if cleaned else None
    return None

db_url = os.getenv('DATABASE_URL', 'postgresql://postgres.smbrfdwruccudlcjdabs:rotary4110creel@aws-0-ca-central-1.pooler.supabase.com:6543/postgres')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif db_url and db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app, engine_options={
    "pool_pre_ping": True,
    "pool_recycle": 300,
})

MESES_CONTROL = [
    "JUN 2025", "JUL 2025", "AGO 2025", "SEP 2025", "OCT 2025", "NOV 2025", "DIC 2025",
    "ENE 2026", "FEB 2026", "MAR 2026", "ABR 2026", "MAY 2026", "JUN 2026",
    "JUL 2026", "AGO 2026", "SEP 2026", "OCT 2026", "NOV 2026", "DIC 2026",
    "ENE 2027", "FEB 2027", "MAR 2027", "ABR 2027", "MAY 2027", "JUN 2027"
]

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(50), default='SOCIO')

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
    nivel = db.Column(db.String(50), nullable=False)
    correo = db.Column(db.String(100))
    telefono = db.Column(db.String(50))

class PagoCuota(db.Model):
    __tablename__ = 'pagos_cuotas'
    id = db.Column(db.Integer, primary_key=True)
    socio_id = db.Column(db.Integer, db.ForeignKey('socios.id'), nullable=False)
    mes_anio = db.Column(db.String(20), nullable=False)
    monto = db.Column(db.Float, default=500.0)
    metodo_pago = db.Column(db.String(50))
    fecha_pago = db.Column(db.Date, default=datetime.utcnow)
    referencia = db.Column(db.String(100))

class ConfiguracionTesoreria(db.Model):
    __tablename__ = 'configuracion_tesoreria'
    id = db.Column(db.Integer, primary_key=True)
    saldo_inicial = db.Column(db.Float, default=0.0)
    fecha_actualizacion = db.Column(db.Date, default=datetime.utcnow)

class Socio(db.Model):
    __tablename__ = 'socios'
    id = db.Column(db.Integer, primary_key=True)
    numero_socio = db.Column(db.String(50))
    nombre_completo = db.Column(db.String(150), nullable=False)
    telefono = db.Column(db.String(50))
    correo = db.Column(db.String(100))
    fecha_nacimiento = db.Column(db.Date)
    es_activo = db.Column(db.Boolean, default=True)
    tipo_socio = db.Column(db.String(50))
    calle_numero = db.Column(db.String(150))
    colonia = db.Column(db.String(100))
    codigo_postal = db.Column(db.String(20))
    ciudad = db.Column(db.String(100))
    estado = db.Column(db.String(100))
    estado_civil = db.Column(db.String(50))
    nombre_esposa = db.Column(db.String(150))
    fecha_nacimiento_esposa = db.Column(db.Date)
    aniversario_matrimonio = db.Column(db.Date)
    telefono_esposa = db.Column(db.String(50))
    telefono_emergencia = db.Column(db.String(50))
    foto_url = db.Column(db.Text)
    cargos = db.relationship('HistorialCargo', backref='socio', lazy=True, cascade="all, delete-orphan")
    hijos = db.relationship('Hijo', backref='socio', lazy=True, cascade="all, delete-orphan")
    pagos = db.relationship('PagoCuota', backref='socio', lazy=True, cascade="all, delete-orphan", passive_deletes=True)

with app.app_context():
    db.create_all()
    try:
        PagoCuota.__table__.create(db.engine, checkfirst=True)
        ConfiguracionTesoreria.__table__.create(db.engine, checkfirst=True)
    except Exception as e:
        print(f"Info tablas tesoreria: {e}")
    try:
        db.session.execute(db.text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS rol VARCHAR(50) DEFAULT 'SOCIO';"))
        db.session.execute(db.text("ALTER TABLE socios DROP CONSTRAINT IF EXISTS socios_numero_socio_key;"))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
    pass_hash = generate_password_hash('rotary2026')
    credenciales = [
        ('admin', pass_hash, 'ADMIN'),
        ('presidente', pass_hash, 'PRESIDENTE'),
        ('tesorero', pass_hash, 'TESORERO'),
        ('rccreel', pass_hash, 'SOCIO')
    ]
    for usr, phash, r in credenciales:
        u_db = Usuario.query.filter_by(username=usr).first()
        if not u_db:
            db.session.add(Usuario(username=usr, password_hash=phash, rol=r))
        else:
            u_db.rol = r
    db.session.commit()
    if not ConfiguracionTesoreria.query.first():
        db.session.add(ConfiguracionTesoreria(saldo_inicial=0.0))
        db.session.commit()

@app.route('/')
def index_publico():
    lista_socios = Socio.query.order_by(Socio.nombre_completo.asc()).all()
    return render_template('publico.html', socios=lista_socios)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = Usuario.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['rol'] = user.rol
            return redirect(url_for('menu_principal'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    return render_template('login.html')

@app.route('/menu-principal')
@app.route('/menu')
def menu_principal():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    lista_socios = Socio.query.order_by(Socio.nombre_completo.asc()).all()
    meses_es = {1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL", 5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO", 9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"}
    mes_actual_num = datetime.now().month
    mes_actual_nombre = meses_es.get(mes_actual_num, "MES")
    festividades = []
    for socio in lista_socios:
        if socio.fecha_nacimiento and socio.fecha_nacimiento.month == mes_actual_num:
            festividades.append({'dia': socio.fecha_nacimiento.day, 'tipo': 'CUMPLEAÑOS SOCIO', 'persona': socio.nombre_completo, 'detalle': f"SOCIO ID: {socio.numero_socio or socio.id}"})
        if socio.fecha_nacimiento_esposa and socio.fecha_nacimiento_esposa.month == mes_actual_num:
            festividades.append({'dia': socio.fecha_nacimiento_esposa.day, 'tipo': 'CUMPLEAÑOS CÓNYUGE', 'persona': socio.nombre_esposa or 'CÓNYUGE', 'detalle': f"CÓNYUGE DE: {socio.nombre_completo}"})
        if socio.aniversario_matrimonio and socio.aniversario_matrimonio.month == mes_actual_num:
            festividades.append({'dia': socio.aniversario_matrimonio.day, 'tipo': 'ANIVERSARIO DE BODAS', 'persona': f"{socio.nombre_completo} Y {socio.nombre_esposa or 'CÓNYUGE'}", 'detalle': "ANIVERSARIO MATRIMONIAL"})
        if socio.hijos:
            for hijo in socio.hijos:
                if hijo.fecha_nacimiento and hijo.fecha_nacimiento.month == mes_actual_num:
                    festividades.append({'dia': hijo.fecha_nacimiento.day, 'tipo': 'CUMPLEAÑOS HIJO(A)', 'persona': hijo.nombre, 'detalle': f"HIJO(A) DE: {socio.nombre_completo}"})
    festividades = sorted(festividades, key=lambda x: x['dia'])
    return render_template('menu_principal.html', mes_actual_nombre=mes_actual_nombre, festividades_mes=festividades)

@app.route('/socios')
def gestion_socios():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    lista_socios = Socio.query.order_by(Socio.nombre_completo.asc()).all()
    meses_es = {1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL", 5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO", 9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"}
    mes_actual_num = datetime.now().month
    mes_actual_nombre = meses_es.get(mes_actual_num, "MES")
    festividades = []
    for socio in lista_socios:
        if socio.fecha_nacimiento and socio.fecha_nacimiento.month == mes_actual_num:
            festividades.append({'dia': socio.fecha_nacimiento.day, 'tipo': 'CUMPLEAÑOS SOCIO', 'persona': socio.nombre_completo, 'detalle': f"SOCIO ID: {socio.numero_socio or socio.id}"})
        if socio.fecha_nacimiento_esposa and socio.fecha_nacimiento_esposa.month == mes_actual_num:
            festividades.append({'dia': socio.fecha_nacimiento_esposa.day, 'tipo': 'CUMPLEAÑOS CÓNYUGE', 'persona': socio.nombre_esposa or 'CÓNYUGE', 'detalle': f"CÓNYUGE DE: {socio.nombre_completo}"})
        if socio.aniversario_matrimonio and socio.aniversario_matrimonio.month == mes_actual_num:
            festividades.append({'dia': socio.aniversario_matrimonio.day, 'tipo': 'ANIVERSARIO DE BODAS', 'persona': f"{socio.nombre_completo} Y {socio.nombre_esposa or 'CÓNYUGE'}", 'detalle': "ANIVERSARIO MATRIMONIAL"})
        if socio.hijos:
            for hijo in socio.hijos:
                if hijo.fecha_nacimiento and hijo.fecha_nacimiento.month == mes_actual_num:
                    festividades.append({'dia': hijo.fecha_nacimiento.day, 'tipo': 'CUMPLEAÑOS HIJO(A)', 'persona': hijo.nombre, 'detalle': f"HIJO(A) DE: {socio.nombre_completo}"})
    festividades = sorted(festividades, key=lambda x: x['dia'])
    return render_template('socios.html', socios=lista_socios, mes_actual_nombre=mes_actual_nombre, festividades_mes=festividades)

@app.route('/socios/agregar', methods=['POST'])
def agregar_socio():
    if 'user_id' not in session or session.get('rol') not in ['ADMIN', 'TESORERO', 'PRESIDENTE']:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('gestion_socios'))
    def parse_date(date_str):
        if date_str:
            try:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return None
        return None
    nuevo = Socio(
        numero_socio=to_upper(request.form.get('numero_socio')),
        nombre_completo=to_upper(request.form.get('nombre_completo')),
        tipo_socio=to_upper(request.form.get('tipo_socio')) or 'ACTIVO',
        telefono=to_upper(request.form.get('telefono')),
        correo=request.form.get('correo'),
        fecha_nacimiento=parse_date(request.form.get('fecha_nacimiento')),
        calle_numero=to_upper(request.form.get('calle_numero')),
        colonia=to_upper(request.form.get('colonia')),
        codigo_postal=to_upper(request.form.get('codigo_postal')),
        ciudad=to_upper(request.form.get('ciudad')) or 'CREEL',
        estado=to_upper(request.form.get('estado')) or 'CHIHUAHUA',
        estado_civil=to_upper(request.form.get('estado_civil')),
        nombre_esposa=to_upper(request.form.get('nombre_esposa')),
        fecha_nacimiento_esposa=parse_date(request.form.get('fecha_nacimiento_esposa')),
        aniversario_matrimonio=parse_date(request.form.get('aniversario_matrimonio')),
        telefono_esposa=to_upper(request.form.get('telefono_esposa')),
        telefono_emergencia=to_upper(request.form.get('telefono_emergencia'))
    )
    foto_archivo = request.files.get('foto_archivo')
    if foto_archivo and foto_archivo.filename and allowed_file(foto_archivo.filename):
        try:
            contenido = foto_archivo.read()
            mime = foto_archivo.mimetype or 'image/jpeg'
            b64 = base64.b64encode(contenido).decode('utf-8')
            nuevo.foto_url = f"data:{mime};base64,{b64}"
        except Exception as e:
            flash(f'Error al procesar foto: {e}', 'warning')
    db.session.add(nuevo)
    db.session.flush()
    cargo_inicial = request.form.get('cargo_inicial')
    periodo_inicial = request.form.get('periodo_inicial') or '2026-2027'
    if cargo_inicial:
        db.session.add(HistorialCargo(socio_id=nuevo.id, cargo=cargo_inicial.upper(), periodo=periodo_inicial.upper(), es_actual=True))
    db.session.commit()
    flash('Socio agregado correctamente.', 'success')
    return redirect(url_for('gestion_socios'))

@app.route('/socios/editar/<int:socio_id>', methods=['POST'])
def editar_socio(socio_id):
    if 'user_id' not in session or session.get('rol') not in ['ADMIN', 'TESORERO', 'PRESIDENTE']:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('gestion_socios'))
    socio = Socio.query.get_or_404(socio_id)
    def parse_date(date_str):
        if date_str:
            try:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return None
        return None
    socio.numero_socio = to_upper(request.form.get('numero_socio')) or socio.numero_socio
    socio.nombre_completo = to_upper(request.form.get('nombre_completo')) or socio.nombre_completo
    socio.tipo_socio = to_upper(request.form.get('tipo_socio')) or socio.tipo_socio
    socio.telefono = to_upper(request.form.get('telefono')) or socio.telefono
    socio.correo = request.form.get('correo') or socio.correo
    socio.fecha_nacimiento = parse_date(request.form.get('fecha_nacimiento')) or socio.fecha_nacimiento
    socio.calle_numero = to_upper(request.form.get('calle_numero')) or socio.calle_numero
    socio.colonia = to_upper(request.form.get('colonia')) or socio.colonia
    socio.codigo_postal = to_upper(request.form.get('codigo_postal')) or socio.codigo_postal
    socio.ciudad = to_upper(request.form.get('ciudad')) or socio.ciudad
    socio.estado = to_upper(request.form.get('estado')) or socio.estado
    socio.estado_civil = to_upper(request.form.get('estado_civil')) or socio.estado_civil
    socio.nombre_esposa = to_upper(request.form.get('nombre_esposa')) or socio.nombre_esposa
    socio.fecha_nacimiento_esposa = parse_date(request.form.get('fecha_nacimiento_esposa')) or socio.fecha_nacimiento_esposa
    socio.aniversario_matrimonio = parse_date(request.form.get('aniversario_matrimonio')) or socio.aniversario_matrimonio
    socio.telefono_esposa = to_upper(request.form.get('telefono_esposa')) or socio.telefono_esposa
    socio.telefono_emergencia = to_upper(request.form.get('telefono_emergencia')) or socio.telefono_emergencia
    foto_archivo = request.files.get('foto_archivo')
    if foto_archivo and foto_archivo.filename and allowed_file(foto_archivo.filename):
        try:
            contenido = foto_archivo.read()
            mime = foto_archivo.mimetype or 'image/jpeg'
            b64 = base64.b64encode(contenido).decode('utf-8')
            socio.foto_url = f"data:{mime};base64,{b64}"
        except Exception as e:
            flash(f'Error al procesar foto: {e}', 'warning')

    # --- MANEJO DE HIJOS ---
    # Editar o eliminar hijos existentes
    for hijo in list(socio.hijos):
        del_key = f'hijo_eliminar_{hijo.id}'
        if request.form.get(del_key) == '1':
            db.session.delete(hijo)
        else:
            nombre_key = f'hijo_nombre_{hijo.id}'
            fecha_key = f'hijo_fecha_{hijo.id}'
            nuevo_nombre = request.form.get(nombre_key)
            if nuevo_nombre:
                hijo.nombre = to_upper(nuevo_nombre)
                hijo.fecha_nacimiento = parse_date(request.form.get(fecha_key)) or hijo.fecha_nacimiento

    # Agregar nuevos hijos (hasta 3 por edición)
    for i in range(1, 4):
        n_nombre = request.form.get(f'nuevo_hijo_nombre_{i}')
        n_fecha = request.form.get(f'nuevo_hijo_fecha_{i}')
        if n_nombre and n_nombre.strip():
            nuevo_hijo = Hijo(
                socio_id=socio.id,
                nombre=to_upper(n_nombre),
                fecha_nacimiento=parse_date(n_fecha)
            )
            db.session.add(nuevo_hijo)

    db.session.commit()
    flash('Socio actualizado correctamente (incluyendo hijos).', 'success')
    return redirect(url_for('gestion_socios'))
    socio = Socio.query.get_or_404(socio_id)
    def parse_date(date_str):
        if date_str:
            try:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return None
        return None
    socio.numero_socio = to_upper(request.form.get('numero_socio')) or socio.numero_socio
    socio.nombre_completo = to_upper(request.form.get('nombre_completo')) or socio.nombre_completo
    socio.tipo_socio = to_upper(request.form.get('tipo_socio')) or socio.tipo_socio
    socio.telefono = to_upper(request.form.get('telefono')) or socio.telefono
    socio.correo = request.form.get('correo') or socio.correo
    socio.fecha_nacimiento = parse_date(request.form.get('fecha_nacimiento')) or socio.fecha_nacimiento
    socio.calle_numero = to_upper(request.form.get('calle_numero')) or socio.calle_numero
    socio.colonia = to_upper(request.form.get('colonia')) or socio.colonia
    socio.codigo_postal = to_upper(request.form.get('codigo_postal')) or socio.codigo_postal
    socio.ciudad = to_upper(request.form.get('ciudad')) or socio.ciudad
    socio.estado = to_upper(request.form.get('estado')) or socio.estado
    socio.estado_civil = to_upper(request.form.get('estado_civil')) or socio.estado_civil
    socio.nombre_esposa = to_upper(request.form.get('nombre_esposa')) or socio.nombre_esposa
    socio.fecha_nacimiento_esposa = parse_date(request.form.get('fecha_nacimiento_esposa')) or socio.fecha_nacimiento_esposa
    socio.aniversario_matrimonio = parse_date(request.form.get('aniversario_matrimonio')) or socio.aniversario_matrimonio
    socio.telefono_esposa = to_upper(request.form.get('telefono_esposa')) or socio.telefono_esposa
    socio.telefono_emergencia = to_upper(request.form.get('telefono_emergencia')) or socio.telefono_emergencia
    foto_archivo = request.files.get('foto_archivo')
    if foto_archivo and foto_archivo.filename and allowed_file(foto_archivo.filename):
        try:
            contenido = foto_archivo.read()
            mime = foto_archivo.mimetype or 'image/jpeg'
            b64 = base64.b64encode(contenido).decode('utf-8')
            socio.foto_url = f"data:{mime};base64,{b64}"
        except Exception as e:
            flash(f'Error al procesar foto: {e}', 'warning')
    db.session.commit()
    flash('Socio actualizado.', 'success')
    return redirect(url_for('gestion_socios'))

@app.route('/cumpleanos-mes')
def cumpleanos_mes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    lista_socios = Socio.query.order_by(Socio.nombre_completo.asc()).all()
    meses_es = {1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL", 5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO", 9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"}
    mes_actual_num = datetime.now().month
    mes_actual_nombre = meses_es.get(mes_actual_num, "MES")
    festividades = []
    for socio in lista_socios:
        if socio.fecha_nacimiento and socio.fecha_nacimiento.month == mes_actual_num:
            festividades.append({'fecha_str': f"{socio.fecha_nacimiento.day:02d}/{socio.fecha_nacimiento.month:02d}/{socio.fecha_nacimiento.year}", 'tipo': 'CUMPLEAÑOS SOCIO', 'persona': socio.nombre_completo, 'detalle': f"SOCIO ID: {socio.numero_socio or socio.id}", 'dia': socio.fecha_nacimiento.day})
        if socio.fecha_nacimiento_esposa and socio.fecha_nacimiento_esposa.month == mes_actual_num:
            festividades.append({'fecha_str': f"{socio.fecha_nacimiento_esposa.day:02d}/{socio.fecha_nacimiento_esposa.month:02d}/{socio.fecha_nacimiento_esposa.year}", 'tipo': 'CUMPLEAÑOS CÓNYUGE', 'persona': socio.nombre_esposa or 'CÓNYUGE', 'detalle': f"CÓNYUGE DE: {socio.nombre_completo}", 'dia': socio.fecha_nacimiento_esposa.day})
        if socio.aniversario_matrimonio and socio.aniversario_matrimonio.month == mes_actual_num:
            festividades.append({'fecha_str': f"{socio.aniversario_matrimonio.day:02d}/{socio.aniversario_matrimonio.month:02d}/{socio.aniversario_matrimonio.year}", 'tipo': 'ANIVERSARIO DE BODAS', 'persona': f"{socio.nombre_completo} Y {socio.nombre_esposa or 'CÓNYUGE'}", 'detalle': "ANIVERSARIO MATRIMONIAL", 'dia': socio.aniversario_matrimonio.day})
        if socio.hijos:
            for hijo in socio.hijos:
                if hijo.fecha_nacimiento and hijo.fecha_nacimiento.month == mes_actual_num:
                    festividades.append({'fecha_str': f"{hijo.fecha_nacimiento.day:02d}/{hijo.fecha_nacimiento.month:02d}/{hijo.fecha_nacimiento.year}", 'tipo': 'CUMPLEAÑOS HIJO(A)', 'persona': hijo.nombre, 'detalle': f"HIJO(A) DE: {socio.nombre_completo}", 'dia': hijo.fecha_nacimiento.day})
    festividades = sorted(festividades, key=lambda x: x['dia'])
    return render_template('cumpleanos.html', festividades=festividades, mes_actual=mes_actual_nombre)

@app.route('/autoridades')
def gestion_autoridades():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    autoridades = AutoridadRotaria.query.order_by(AutoridadRotaria.nivel.asc(), AutoridadRotaria.nombre.asc()).all()
    return render_template('autoridades.html', autoridades=autoridades)

@app.route('/autoridades/guardar', methods=['POST'])
def guardar_autoridad():
    if 'user_id' not in session or session.get('rol') not in ['ADMIN', 'PRESIDENTE']:
        flash('No autorizado.', 'danger')
        return redirect(url_for('gestion_autoridades'))
    nombre = to_upper(request.form.get('nombre'))
    cargo = to_upper(request.form.get('cargo'))
    nivel = to_upper(request.form.get('nivel'))
    correo = request.form.get('correo')
    telefono = request.form.get('telefono')
    if nombre and cargo and nivel:
        db.session.add(AutoridadRotaria(nombre=nombre, cargo=cargo, nivel=nivel, correo=correo, telefono=telefono))
        db.session.commit()
        flash('Autoridad guardada.', 'success')
    return redirect(url_for('gestion_autoridades'))

@app.route('/autoridades/eliminar/<int:id>', methods=['POST'])
def eliminar_autoridad(id):
    if 'user_id' not in session or session.get('rol') not in ['ADMIN', 'PRESIDENTE']:
        flash('No autorizado.', 'danger')
        return redirect(url_for('gestion_autoridades'))
    aut = AutoridadRotaria.query.get_or_404(id)
    db.session.delete(aut)
    db.session.commit()
    flash('Autoridad eliminada.', 'warning')
    return redirect(url_for('gestion_autoridades'))

@app.route('/tesoreria')
def modulo_tesoreria():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('tesoreria_menu.html')

@app.route('/tesoreria/cuotas-sociales')
def cuotas_sociales():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    socios = Socio.query.filter_by(es_activo=True).order_by(Socio.nombre_completo.asc()).all()
    config_teso = ConfiguracionTesoreria.query.first()
    saldo_inicial = config_teso.saldo_inicial if config_teso else 0.0
    total_recaudado = PagoCuota.query.filter(PagoCuota.mes_anio.in_(MESES_CONTROL)).with_entities(db.func.sum(PagoCuota.monto)).scalar() or 0.0
    saldo_total_general = saldo_inicial + total_recaudado
    recibo_ids = request.args.get('recibo_ids')
    pagos_recibo = []
    if recibo_ids:
        try:
            ids = [int(x) for x in recibo_ids.split(',') if x]
            pagos_recibo = PagoCuota.query.filter(PagoCuota.id.in_(ids)).all()
        except:
            pagos_recibo = []
    recibo_id = request.args.get('recibo_id')
    if recibo_id and not pagos_recibo:
        p = PagoCuota.query.get(recibo_id)
        if p:
            pagos_recibo = [p]
    ultimo_pago = pagos_recibo[-1] if pagos_recibo else None
    return render_template('tesoreria.html', socios=socios, meses=MESES_CONTROL, ultimo_pago=ultimo_pago, pagos_recibo=pagos_recibo, saldo_inicial=saldo_inicial, saldo_total_general=saldo_total_general)

@app.route('/tesoreria/actualizar-saldo-inicial', methods=['POST'])
def actualizar_saldo_inicial():
    if 'user_id' not in session or session.get('rol') not in ['ADMIN', 'TESORERO', 'PRESIDENTE']:
        flash('No autorizado.', 'danger')
        return redirect(url_for('menu_principal'))
    password = request.form.get('password')
    try:
        nuevo_saldo = float(request.form.get('saldo_inicial', 0.0))
    except:
        flash('Saldo inválido', 'danger')
        return redirect(url_for('cuotas_sociales'))
    user = Usuario.query.get(session['user_id'])
    if user and check_password_hash(user.password_hash, password):
        config = ConfiguracionTesoreria.query.first()
        if not config:
            config = ConfiguracionTesoreria(saldo_inicial=nuevo_saldo)
            db.session.add(config)
        else:
            config.saldo_inicial = nuevo_saldo
        db.session.commit()
        flash('¡Saldo inicial actualizado exitosamente!', 'success')
    else:
        flash('Contraseña incorrecta.', 'danger')
    return redirect(url_for('cuotas_sociales'))

@app.route('/tesoreria/registrar-pago', methods=['POST'])
def registrar_pago_cuota():
    if 'user_id' not in session or session.get('rol') not in ['ADMIN', 'TESORERO', 'PRESIDENTE']:
        flash('No autorizado.', 'danger')
        return redirect(url_for('menu_principal'))
    socio_id = request.form.get('socio_id')
    meses_pagados = request.form.getlist('meses')
    metodo = to_upper(request.form.get('metodo_pago'))
    referencia = to_upper(request.form.get('referencia'))
    if not socio_id or not meses_pagados:
        flash('Debe seleccionar al menos un mes y un socio.', 'warning')
        return redirect(url_for('cuotas_sociales'))
    pagos_creados_ids = []
    for m in meses_pagados:
        mes_limpio = m.strip().upper()
        existente = PagoCuota.query.filter_by(socio_id=socio_id, mes_anio=mes_limpio).first()
        if not existente:
            pago = PagoCuota(socio_id=socio_id, mes_anio=mes_limpio, monto=500.0, metodo_pago=metodo, referencia=referencia)
            db.session.add(pago)
            db.session.flush()
            pagos_creados_ids.append(str(pago.id))
    db.session.commit()
    if pagos_creados_ids:
        flash(f'{len(pagos_creados_ids)} pago(s) registrado(s) correctamente.', 'success')
        return redirect(url_for('cuotas_sociales', recibo_ids=','.join(pagos_creados_ids)))
    else:
        flash('Todos los meses seleccionados ya estaban pagados.', 'info')
        return redirect(url_for('cuotas_sociales'))

@app.route('/tesoreria/editar-pago/<int:pago_id>', methods=['POST'])
def editar_pago_cuota(pago_id):
    if 'user_id' not in session or session.get('rol') not in ['ADMIN', 'TESORERO', 'PRESIDENTE']:
        flash('No autorizado.', 'danger')
        return redirect(url_for('menu_principal'))
    pago = PagoCuota.query.get_or_404(pago_id)
    if request.form.get('accion') == 'eliminar':
        db.session.delete(pago)
        flash('Pago eliminado.', 'warning')
    else:
        try:
            pago.monto = float(request.form.get('monto', 500.0))
        except:
            pago.monto = 500.0
        pago.metodo_pago = to_upper(request.form.get('metodo_pago'))
        pago.referencia = to_upper(request.form.get('referencia'))
        flash('Pago actualizado.', 'success')
    db.session.commit()
    return redirect(url_for('cuotas_sociales'))

@app.route('/tesoreria/recibo/<int:pago_id>')
def ver_recibo(pago_id):
    if 'user_id' not in session or session.get('rol') not in ['ADMIN', 'TESORERO', 'PRESIDENTE']:
        return redirect(url_for('login'))
    pago = PagoCuota.query.get_or_404(pago_id)
    pagos_relacionados = request.args.get('ids')
    if pagos_relacionados:
        try:
            ids = [int(x) for x in pagos_relacionados.split(',') if x]
            pagos = PagoCuota.query.filter(PagoCuota.id.in_(ids)).all()
        except:
            pagos = [pago]
    else:
        pagos = [pago]
    meses_es = { "January": "ENERO", "February": "FEBRERO", "March": "MARZO", "April": "ABRIL", "May": "MAYO", "June": "JUNIO", "July": "JULIO", "August": "AGOSTO", "September": "SEPTIEMBRE", "October": "OCTUBRE", "November": "NOVIEMBRE", "December": "DICIEMBRE" }
    dias_es = { "Monday": "LUNES", "Tuesday": "MARTES", "Wednesday": "MIÉRCOLES", "Thursday": "JUEVES", "Friday": "VIERNES", "Saturday": "SÁBADO", "Sunday": "DOMINGO" }
    ahora = datetime.now()
    fecha_recibo = f"{dias_es.get(ahora.strftime('%A'), '')}, {ahora.day} DE {meses_es.get(ahora.strftime('%B'), '')} DE {ahora.year}"
    total = sum(p.monto for p in pagos)
    return render_template('recibo_pdf.html', pago=pago, pagos=pagos, total=total, fecha_recibo=fecha_recibo)

@app.route('/tesoreria/estado-cuenta-pdf/<int:socio_id>')
def estado_cuenta_pdf(socio_id):
    if 'user_id' not in session or session.get('rol') not in ['ADMIN', 'TESORERO', 'PRESIDENTE']:
        return redirect(url_for('login'))
    socio = Socio.query.get_or_404(socio_id)
    meses_es = {"January": "ENERO", "February": "FEBRERO", "March": "MARZO", "April": "ABRIL", "May": "MAYO", "June": "JUNIO", "July": "JULIO", "August": "AGOSTO", "September": "SEPTIEMBRE", "October": "OCTUBRE", "November": "NOVIEMBRE", "December": "DICIEMBRE"}
    dias_es = {"Monday": "LUNES", "Tuesday": "MARTES", "Wednesday": "MIÉRCOLES", "Thursday": "JUEVES", "Friday": "VIERNES", "Saturday": "SÁBADO", "Sunday": "DOMINGO"}
    ahora = datetime.now()
    fecha_actual_str = f"{dias_es.get(ahora.strftime('%A'), '')}, {ahora.day} DE {meses_es.get(ahora.strftime('%B'), '')} DE {ahora.year}"
    return render_template('estado_cuenta_pdf.html', socio=socio, meses=MESES_CONTROL, fecha_actual_str=fecha_actual_str)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index_publico'))

if __name__ == '__main__':
    app.run(debug=True)
