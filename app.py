from sqlalchemy import func
from flask import Flask, render_template, render_template_string, request, redirect, url_for, session, flash
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

MESES_NOMBRES = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)  # = numero_socio para socios, o admin/presidente/tesorero
    password_hash = db.Column(db.String(255), nullable=True)  # NULL = sin contraseña, debe crearla en primer ingreso
    rol = db.Column(db.String(50), default='SOCIO')
    socio_id = db.Column(db.Integer, db.ForeignKey('socios.id'), nullable=True)
    debe_crear_password = db.Column(db.Boolean, default=True)  # True = primer ingreso / reseteado por ADMIN
    fecha_creacion_password = db.Column(db.DateTime, nullable=True)
    socio = db.relationship('Socio', backref='usuario', uselist=False)

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

# ==================== NUEVOS MODELOS GASTOS Y PROYECTOS ====================
class Proyecto(db.Model):
    __tablename__ = 'proyectos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)  # PROYECTO BOMBERA
    descripcion = db.Column(db.Text, nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)
    eventos = db.relationship('EventoProyecto', backref='proyecto', cascade='all, delete-orphan', lazy=True)
    gastos = db.relationship('Gasto', backref='proyecto_rel', lazy=True)

class EventoProyecto(db.Model):
    __tablename__ = 'eventos_proyecto'
    id = db.Column(db.Integer, primary_key=True)
    proyecto_id = db.Column(db.Integer, db.ForeignKey('proyectos.id'), nullable=False)
    nombre = db.Column(db.String(200), nullable=False)  # Cena Gala, Rifa, Boteo
    descripcion = db.Column(db.Text, nullable=True)
    monto_meta = db.Column(db.Float, nullable=False)  # Monto a recaudar
    monto_recaudado = db.Column(db.Float, default=0.0)
    fecha_evento = db.Column(db.Date, nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    detalle_recaudado = db.Column(db.Text, nullable=True)  # Detalle numerico
    @property
    def porcentaje_meta(self):
        return (self.monto_recaudado / self.monto_meta * 100) if self.monto_meta > 0 else 0
    @property
    def faltante(self):
        return self.monto_meta - self.monto_recaudado

class Gasto(db.Model):
    __tablename__ = 'gastos'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    mes_anio = db.Column(db.String(20), nullable=False)  # OCT 2026
    concepto = db.Column(db.String(300), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    centro_costo = db.Column(db.String(30), nullable=False)  # ADMINISTRATIVO o PROYECTO
    proyecto_id = db.Column(db.Integer, db.ForeignKey('proyectos.id'), nullable=True)
    comprobante = db.Column(db.String(300), nullable=True)
    foto_comprobante = db.Column(db.Text, nullable=True)  # Base64 de foto ticket/factura
    creado_por = db.Column(db.String(100), nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    notas = db.Column(db.Text, nullable=True)

class IngresoExtraordinario(db.Model):
    __tablename__ = 'ingresos_extraordinarios'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    mes_anio = db.Column(db.String(20), nullable=False)  # NOV 2026
    concepto = db.Column(db.String(300), nullable=False)  # DONACION EMPRESA X, VENTA BOLETOS, etc
    monto = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.String(50), nullable=False, default='DONACION')  # DONACION, PATROCINIO, VENTA, APORTACION, RIFA, OTRO
    origen = db.Column(db.String(200), nullable=True)  # Quien dona / de donde viene
    referencia = db.Column(db.String(300), nullable=True)
    comprobante_nombre = db.Column(db.String(300), nullable=True)
    comprobante_base64 = db.Column(db.Text, nullable=True)  # PDF o imagen en base64
    registrado_por = db.Column(db.String(100), nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    notas = db.Column(db.Text, nullable=True)

class DocumentoRotario(db.Model):
    __tablename__ = 'documentos_rotarios'
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False, default='ACTA')  # ACTA, ACUERDO, PRESIDENCIA, SECRETARIA, FUNDACION, SERVICIOS, TESORERIA, MEMBRESIA, OTRO
    titulo = db.Column(db.String(300), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    fecha_documento = db.Column(db.Date, nullable=True)
    estado = db.Column(db.String(20), nullable=False, default='VIGENTE')  # VIGENTE, ARCHIVADO, BORRADOR
    archivo_nombre = db.Column(db.String(300), nullable=True)
    archivo_base64 = db.Column(db.Text, nullable=True)
    subido_por = db.Column(db.String(100), nullable=True)
    fecha_subida = db.Column(db.DateTime, default=datetime.utcnow)
    # SEGUIMIENTO / EVENTO
    tiene_fechas = db.Column(db.Boolean, default=False)
    fecha_inicio = db.Column(db.Date, nullable=True)
    fecha_termino = db.Column(db.Date, nullable=True)
    responsable = db.Column(db.String(150), nullable=True)
    prioridad = db.Column(db.String(20), default='MEDIA')
    porcentaje_avance = db.Column(db.Integer, default=0)
    # FECHA DE EJECUCION - para scroll en menu principal junto con cumpleaños
    tiene_fecha_ejecucion = db.Column(db.Boolean, default=False)
    fecha_ejecucion = db.Column(db.Date, nullable=True)

with app.app_context():
    db.create_all()
    try:
        PagoCuota.__table__.create(db.engine, checkfirst=True)
        ConfiguracionTesoreria.__table__.create(db.engine, checkfirst=True)
        Proyecto.__table__.create(db.engine, checkfirst=True)
        EventoProyecto.__table__.create(db.engine, checkfirst=True)
        Gasto.__table__.create(db.engine, checkfirst=True)
        IngresoExtraordinario.__table__.create(db.engine, checkfirst=True)
        DocumentoRotario.__table__.create(db.engine, checkfirst=True)
    except Exception as e:
        print(f"Info tablas: {e}")
    try:
        db.session.execute(db.text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS rol VARCHAR(50) DEFAULT 'SOCIO';"))
        db.session.execute(db.text("ALTER TABLE socios DROP CONSTRAINT IF EXISTS socios_numero_socio_key;"))
        # MIGRACION TABLA INGRESOS_EXTRAORDINARIOS - agregar columnas si faltan (fix UndefinedColumn origen)
        db.session.execute(db.text("ALTER TABLE ingresos_extraordinarios ADD COLUMN IF NOT EXISTS fecha DATE;"))
        db.session.execute(db.text("ALTER TABLE ingresos_extraordinarios ADD COLUMN IF NOT EXISTS mes_anio VARCHAR(20);"))
        db.session.execute(db.text("ALTER TABLE ingresos_extraordinarios ADD COLUMN IF NOT EXISTS concepto VARCHAR(300);"))
        db.session.execute(db.text("ALTER TABLE ingresos_extraordinarios ADD COLUMN IF NOT EXISTS monto FLOAT;"))
        db.session.execute(db.text("ALTER TABLE ingresos_extraordinarios ADD COLUMN IF NOT EXISTS tipo VARCHAR(50) DEFAULT 'DONACION';"))
        db.session.execute(db.text("ALTER TABLE ingresos_extraordinarios ADD COLUMN IF NOT EXISTS origen VARCHAR(200);"))
        db.session.execute(db.text("ALTER TABLE ingresos_extraordinarios ADD COLUMN IF NOT EXISTS referencia VARCHAR(300);"))
        db.session.execute(db.text("ALTER TABLE ingresos_extraordinarios ADD COLUMN IF NOT EXISTS comprobante_nombre VARCHAR(300);"))
        db.session.execute(db.text("ALTER TABLE ingresos_extraordinarios ADD COLUMN IF NOT EXISTS comprobante_base64 TEXT;"))
        db.session.execute(db.text("ALTER TABLE ingresos_extraordinarios ADD COLUMN IF NOT EXISTS registrado_por VARCHAR(100);"))
        db.session.execute(db.text("ALTER TABLE ingresos_extraordinarios ADD COLUMN IF NOT EXISTS fecha_creacion TIMESTAMP DEFAULT NOW();"))
        db.session.execute(db.text("ALTER TABLE ingresos_extraordinarios ADD COLUMN IF NOT EXISTS notas TEXT;"))
        db.session.execute(db.text("ALTER TABLE gastos ADD COLUMN IF NOT EXISTS foto_comprobante TEXT;"))
        db.session.execute(db.text("ALTER TABLE documentos_rotarios ADD COLUMN IF NOT EXISTS tiene_fechas BOOLEAN DEFAULT FALSE;"))
        db.session.execute(db.text("ALTER TABLE documentos_rotarios ADD COLUMN IF NOT EXISTS fecha_inicio DATE;"))
        db.session.execute(db.text("ALTER TABLE documentos_rotarios ADD COLUMN IF NOT EXISTS fecha_termino DATE;"))
        db.session.execute(db.text("ALTER TABLE documentos_rotarios ADD COLUMN IF NOT EXISTS responsable VARCHAR(150);"))
        db.session.execute(db.text("ALTER TABLE documentos_rotarios ADD COLUMN IF NOT EXISTS prioridad VARCHAR(20) DEFAULT 'MEDIA';"))
        db.session.execute(db.text("ALTER TABLE documentos_rotarios ADD COLUMN IF NOT EXISTS porcentaje_avance INTEGER DEFAULT 0;"))
        db.session.execute(db.text("ALTER TABLE documentos_rotarios ADD COLUMN IF NOT EXISTS tiene_fecha_ejecucion BOOLEAN DEFAULT FALSE;"))
        db.session.execute(db.text("ALTER TABLE documentos_rotarios ADD COLUMN IF NOT EXISTS fecha_ejecucion DATE;"))
        db.session.execute(db.text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS socio_id INTEGER;"))
        db.session.execute(db.text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS debe_crear_password BOOLEAN DEFAULT TRUE;"))
        db.session.execute(db.text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS fecha_creacion_password TIMESTAMP;"))
        # password_hash ahora puede ser NULL (sin contraseña = primer ingreso)
        db.session.execute(db.text("ALTER TABLE usuarios ALTER COLUMN password_hash DROP NOT NULL;"))
        db.session.commit()
    except Exception as e:
        print(f"Migracion ingresos_extraordinarios: {e}")
        db.session.rollback()
    pass_hash = generate_password_hash('rotary2026')
    credenciales = [
        ('admin', pass_hash, 'ADMIN'),
        ('presidente', pass_hash, 'PRESIDENTE'),
        ('tesorero', pass_hash, 'TESORERO'),
        ('rccreel', pass_hash, 'SOCIO')
    ]
    for usr, phash, r in credenciales:
        u_db = Usuario.query.filter(func.lower(Usuario.username) == usr.lower()).first()
        if not u_db:
            db.session.add(Usuario(username=usr, password_hash=phash, rol=r, debe_crear_password=False))
        else:
            u_db.rol = r
            # REPARACION: si la cuenta fija quedo sin contraseña por la migracion (DEFAULT TRUE), restaurarla
            if not u_db.password_hash:
                u_db.password_hash = phash
            # Los fijos ya tienen contraseña, nunca pedir crear
            u_db.debe_crear_password = False
    db.session.commit()
    # SINCRONIZAR USUARIOS DESDE SOCIOS - numero_socio = username
    try:
        for s in Socio.query.all():
            if not s.numero_socio:
                continue
            uname = s.numero_socio.strip().upper()
            if not Usuario.query.filter_by(username=uname).first():
                db.session.add(Usuario(username=uname, password_hash=None, rol='SOCIO', socio_id=s.id, debe_crear_password=True))
        db.session.commit()
    except Exception as e:
        print(f"Sync usuarios socios: {e}")
        db.session.rollback()
    if not ConfiguracionTesoreria.query.first():
        db.session.add(ConfiguracionTesoreria(saldo_inicial=0.0))
        db.session.commit()
    # Crear PROYECTO BOMBERA si no existe
    if not Proyecto.query.filter_by(nombre='PROYECTO BOMBERA').first():
        p = Proyecto(nombre='PROYECTO BOMBERA', descripcion='Proyecto activo recaudacion para bomberos Creel', activo=True)
        db.session.add(p)
        db.session.commit()


def crear_usuario_para_socio(socio):
    """Crea usuario con username=numero_socio, sin contraseña, debe crearla en primer ingreso."""
    if not socio or not socio.numero_socio:
        return None
    uname = socio.numero_socio.strip().upper()
    existente = Usuario.query.filter(func.lower(Usuario.username) == uname.lower()).first()
    if existente:
        if not existente.socio_id:
            existente.socio_id = socio.id
            db.session.commit()
        return existente
    nuevo_u = Usuario(username=uname, password_hash=None, rol='SOCIO', socio_id=socio.id, debe_crear_password=True)
    db.session.add(nuevo_u)
    db.session.commit()
    return nuevo_u


def validar_password_segura(pw):
    """Regla 8+1+1: min 8 caracteres, al menos 1 MAYUSCULA y al menos 1 NUMERO."""
    if not pw or len(pw) < 8:
        return False, 'La contraseña debe tener al menos 8 caracteres.'
    if not any(ch.isupper() for ch in pw):
        return False, 'La contraseña debe tener al menos 1 MAYUSCULA.'
    if not any(ch.isdigit() for ch in pw):
        return False, 'La contraseña debe tener al menos 1 NUMERO.'
    return True, ''


ROLES_TESORERIA = ['ADMIN', 'PRESIDENTE', 'TESORERO']
def es_mi_socio(socio):
    """True si el usuario logueado es ese socio (excepto ADMIN que puede todos)."""
    if session.get('rol') == 'ADMIN':
        return True
    if not socio:
        return False
    u = Usuario.query.get(session.get('user_id')) if session.get('user_id') else None
    if u and u.socio_id and u.socio_id == socio.id:
        return True
    if socio.numero_socio and session.get('username') and socio.numero_socio.strip().upper() == session.get('username','').strip().upper():
        return True
    return False

def puede_tesoreria():
    return session.get('rol') in ROLES_TESORERIA

def solo_estado_cuenta():
    """Si es SOCIO (no ADMIN/PRESIDENTE/TESORERO), no puede ver tesoreria completa, solo estados de cuenta."""
    if session.get('rol') not in ROLES_TESORERIA:
        flash('Como SOCIO solo puedes ver ESTADOS DE CUENTA (mensual y meses anteriores).', 'warning')
        return True
    return False



def _fecha_ejecucion_form():
    """Toma el ultimo valor no vacio de fecha_ejecucion (por si el form trae duplicados)."""
    vals = request.form.getlist('fecha_ejecucion') if hasattr(request.form, 'getlist') else [request.form.get('fecha_ejecucion')]
    for v in reversed(vals):
        if v and v.strip():
            try:
                return datetime.strptime(v.strip(), '%Y-%m-%d').date()
            except:
                continue
    return None

def get_mes_anio_actual():
    now = datetime.now()
    return f"{MESES_NOMBRES[now.month-1]} {now.year}"

@app.route('/')
def index_publico():
    lista_socios = Socio.query.order_by(Socio.nombre_completo.asc()).all()
    return render_template('publico.html', socios=lista_socios)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_raw = request.form['username'].strip()
        username = username_raw.upper()
        password = request.form.get('password','')
        # FIX: busqueda sin importar mayusculas - "admin" en BD vs "ADMIN" que escribia el usuario
        user = Usuario.query.filter(func.lower(Usuario.username) == username_raw.lower()).first()
        if user:
            username = user.username  # usar como esta guardado: admin, PRESIDENTE, 5, etc.
        if not user:
            # Intentar sincronizar por si el socio se acaba de crear
            socio = Socio.query.filter(func.lower(Socio.numero_socio) == username_raw.lower()).first()
            if socio:
                user = crear_usuario_para_socio(socio)
                if user:
                    username = user.username
        if not user:
            flash('Usuario no encontrado. Tu usuario es tu NUMERO DE SOCIO. Pregunta a ADMIN si no lo tienes.', 'danger')
            return render_template('login.html')
        # PRIMER INGRESO O RESETEADO POR ADMIN - sin contraseña
        # FIX: cuentas fijas (admin/presidente/tesorero) nunca van a crear-password si ya tienen hash
        if user.username.lower() in ('admin','presidente','tesorero','rccreel') and user.password_hash:
            user.debe_crear_password = False
            db.session.commit()
        if user.debe_crear_password or not user.password_hash:
            session['pending_user_id'] = user.id
            session['pending_username'] = user.username
            flash(f'Hola {user.username}, es tu primer ingreso. Crea tu contraseña.', 'info')
            return redirect(url_for('crear_password'))
        if user.password_hash and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['rol'] = user.rol
            session.pop('pending_user_id', None)
            return redirect(url_for('menu_principal'))
        else:
            flash('Contraseña incorrecta. Si la olvidaste, pide a ADMIN que la borre para crear una nueva.', 'danger')
    try:
        return render_template('login.html')
    except Exception:
        return render_template_string('<h3>LOGIN ROTARY CREEL</h3><form method="POST"><label>USUARIO (NUMERO DE SOCIO):</label><input name="username" required><br><label>CONTRASEÑA:</label><input type="password" name="password"><br><button>INGRESAR</button></form><p>⚠️ Falta subir login.html a Render</p>')

@app.route('/crear-password', methods=['GET', 'POST'])
def crear_password():
    # Solo quien esta en primer ingreso / reseteado puede entrar aqui
    pending_id = session.get('pending_user_id')
    if not pending_id:
        return redirect(url_for('login'))
    user = Usuario.query.get(pending_id)
    if not user:
        session.pop('pending_user_id', None)
        return redirect(url_for('login'))
    # Si ya tiene contraseña y no debe crear, volver a login
    if user.password_hash and not user.debe_crear_password:
        return redirect(url_for('login'))
    if request.method == 'POST':
        pw1 = request.form.get('password1','')
        pw2 = request.form.get('password2','')
        ok, msg = validar_password_segura(pw1)
        if not ok:
            flash(f'{msg} Regla: 8+1+1 = min 8 caracteres, 1 MAYUSCULA y 1 NUMERO. Ej: Rotary2026', 'danger')
            return render_template('crear_password.html', username=user.username)
        if pw1 != pw2:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('crear_password.html', username=user.username)
        user.password_hash = generate_password_hash(pw1)
        user.debe_crear_password = False
        user.fecha_creacion_password = datetime.now()
        db.session.commit()
        session['user_id'] = user.id
        session['username'] = user.username
        session['rol'] = user.rol
        session.pop('pending_user_id', None)
        session.pop('pending_username', None)
        flash(f'Contraseña creada. Bienvenido {user.username}!', 'success')
        return redirect(url_for('menu_principal'))
    try:
        return render_template('crear_password.html', username=user.username)
    except Exception:
        return render_template_string(f'<h3>CREA TU CONTRASEÑA - {user.username}</h3><form method="POST"><label>NUEVA CONTRASEÑA (min 8, 1 MAYUSCULA y 1 NUMERO):</label><input type="password" name="password1" required><br><label>REPITE:</label><input type="password" name="password2" required><br><button>CREAR CONTRASEÑA</button></form><p>⚠️ Falta subir crear_password.html a Render</p>')

@app.route('/admin/usuarios')
def admin_usuarios():
    if 'user_id' not in session or session.get('rol') != 'ADMIN':
        flash('Solo ADMIN puede ver usuarios.', 'danger')
        return redirect(url_for('menu_principal'))
    usuarios = Usuario.query.order_by(Usuario.username.asc()).all()
    socios = Socio.query.order_by(Socio.numero_socio.asc()).all()
    try:
        return render_template('admin_usuarios.html', usuarios=usuarios, socios=socios)
    except Exception:
        # FALLBACK: si admin_usuarios.html no se subio a Render, no dar 500
        filas = ""
        for u in usuarios:
            nombre = u.socio.nombre_completo if getattr(u, 'socio', None) else '- CUENTA FIJA -'
            estado = '⏳ SIN CONTRASEÑA - DEBE CREARLA' if (u.debe_crear_password or not u.password_hash) else '✅ TIENE CONTRASEÑA'
            btn = f'<form method="POST" action="/admin/usuarios/cambiar/{u.id}" style="display:inline;"><input name="nueva_password" placeholder="Nueva (8+1+1)" style="width:110px;font-size:11px;" required><button class="btn btn-warning btn-sm fw-bold">✏️ CAMBIAR</button></form> <form method="POST" action="/admin/usuarios/reset/{u.id}" style="display:inline;"><button class="btn btn-danger btn-sm fw-bold">🗑️ BORRAR</button></form>'
            filas += f"<tr><td><b>{u.username}</b></td><td>{u.rol}</td><td>{nombre}</td><td>{estado}</td><td>{btn}</td></tr>"
        html = f'''<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>Usuarios - ADMIN</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head><body><div class="container py-3"><div class="alert alert-warning">⚠️ Falta subir <b>admin_usuarios.html</b> a Render. Esta es la vista de emergencia, funciona igual para borrar contraseñas.</div><a href="/menu" class="btn btn-secondary btn-sm">MENÚ</a><form method="POST" action="/admin/usuarios/crear-faltantes" class="my-3"><button class="btn btn-success btn-sm fw-bold">+ CREAR USUARIOS FALTANTES</button></form><table class="table table-bordered bg-white"><thead style="background:#17458F;color:white;"><tr><th>USUARIO</th><th>ROL</th><th>SOCIO</th><th>ESTADO</th><th>ACCION</th></tr></thead><tbody>{filas}</tbody></table></div></body></html>'''
        return render_template_string(html)

@app.route('/admin/usuarios/reset/<int:user_id>', methods=['POST'])
def admin_reset_password(user_id):
    # SOLO ADMIN puede borrar el campo de contraseña
    if 'user_id' not in session or session.get('rol') != 'ADMIN':
        flash('Solo ADMIN puede resetear contraseñas.', 'danger')
        return redirect(url_for('menu_principal'))
    user = Usuario.query.get_or_404(user_id)
    # AHORA SI se puede borrar incluso cuentas fijas - lo pidio el ADMIN
    # Si ADMIN se borra a si mismo, en su proximo login creara contraseña nueva
    user.password_hash = None
    user.debe_crear_password = True
    user.fecha_creacion_password = None
    db.session.commit()
    flash(f'Contraseña de {user.username} borrada. El socio la creara de nuevo en su proximo ingreso.', 'success')
    return redirect(url_for('admin_usuarios'))

@app.route('/admin/usuarios/cambiar/<int:user_id>', methods=['POST'])
def admin_cambiar_password(user_id):
    # SOLO ADMIN puede ver/editar/cambiar contraseña de cualquier usuario, incluidas fijas
    if 'user_id' not in session or session.get('rol') != 'ADMIN':
        flash('Solo ADMIN puede cambiar contraseñas.', 'danger')
        return redirect(url_for('menu_principal'))
    user = Usuario.query.get_or_404(user_id)
    nueva = request.form.get('nueva_password','').strip()
    ok, msg = validar_password_segura(nueva)
    if not ok:
        flash(f'No se cambio {user.username}: {msg} Regla 8+1+1 = min 8, 1 MAYUSCULA y 1 NUMERO. Ej: Rotary2026', 'danger')
        return redirect(url_for('admin_usuarios'))
    user.password_hash = generate_password_hash(nueva)
    user.debe_crear_password = False
    user.fecha_creacion_password = datetime.now()
    db.session.commit()
    flash(f'Contraseña de {user.username} cambiada por ADMIN. Ya puede entrar con la nueva.', 'success')
    return redirect(url_for('admin_usuarios'))

@app.route('/admin/usuarios/eliminar/<int:user_id>', methods=['POST'])
def admin_eliminar_usuario(user_id):
    if 'user_id' not in session or session.get('rol') != 'ADMIN':
        return redirect(url_for('menu_principal'))
    user = Usuario.query.get_or_404(user_id)
    if user.username.lower() == 'admin':
        flash('No puedes eliminar tu propia cuenta ADMIN.', 'danger')
        return redirect(url_for('admin_usuarios'))
    # Si es duplicado RCREEL/RCCREEL o socio dado de baja, ADMIN puede eliminarlo
    nombre = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'Usuario {nombre} eliminado por ADMIN.', 'warning')
    return redirect(url_for('admin_usuarios'))

@app.route('/admin/usuarios/crear-faltantes', methods=['POST'])
def admin_crear_faltantes():
    if 'user_id' not in session or session.get('rol') != 'ADMIN':
        return redirect(url_for('menu_principal'))
    creados = 0
    for s in Socio.query.all():
        if s.numero_socio and not Usuario.query.filter_by(username=s.numero_socio.strip().upper()).first():
            crear_usuario_para_socio(s)
            creados += 1
    flash(f'{creados} usuarios creados desde socios.', 'success')
    return redirect(url_for('admin_usuarios'))

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
    # EVENTOS CON FECHA DE EJECUCION EN ESTE MES - para scroll junto con cumpleaños
    try:
        eventos_mes = DocumentoRotario.query.all()
        _vistos = set()
        for ev in eventos_mes:
            # 1) Fecha de ejecucion (la que manda)
            if ev.fecha_ejecucion and ev.fecha_ejecucion.month == mes_actual_num and ev.fecha_ejecucion.year == datetime.now().year:
                festividades.append({'dia': ev.fecha_ejecucion.day, 'tipo': '📅 EVENTO / FECHA DE EJECUCION', 'persona': ev.titulo, 'detalle': f"{ev.tipo} - EJECUCION: {ev.fecha_ejecucion.strftime('%d/%m/%Y')} - {ev.descripcion[:80] if ev.descripcion else ''}", 'es_evento': True, 'doc_id': ev.id})
                _vistos.add(ev.id)
            # 2) Respaldo: si no tiene ejecucion pero si fecha_inicio en este mes, mostrarlo tambien (no duplicar)
            elif ev.id not in _vistos and ev.fecha_inicio and ev.fecha_inicio.month == mes_actual_num and ev.fecha_inicio.year == datetime.now().year:
                festividades.append({'dia': ev.fecha_inicio.day, 'tipo': '📅 EVENTO / FECHA INICIO', 'persona': ev.titulo, 'detalle': f"{ev.tipo} - INICIO: {ev.fecha_inicio.strftime('%d/%m/%Y')} - {ev.descripcion[:80] if ev.descripcion else ''}", 'es_evento': True, 'doc_id': ev.id})
                _vistos.add(ev.id)
    except Exception as e:
        print(f"Eventos ejecucion: {e}")
    festividades = sorted(festividades, key=lambda x: x['dia'])
    return render_template('menu_principal.html', mes_actual_nombre=mes_actual_nombre, festividades_mes=festividades)

@app.route('/socios')
def gestion_socios():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    lista_socios = Socio.query.order_by(Socio.nombre_completo.asc()).all()
    # CALCULAR FESTIVIDADES DEL MES (CUMPLEAÑOS) - FIX QUE NO MOSTRABA
    meses_es = {1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL", 5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO", 9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"}
    mes_actual_num = datetime.now().month
    mes_actual_nombre = meses_es.get(mes_actual_num, "MES")
    festividades = []
    for socio in lista_socios:
        if socio.fecha_nacimiento and socio.fecha_nacimiento.month == mes_actual_num:
            festividades.append({'dia': socio.fecha_nacimiento.day, 'tipo': 'CUMPLEAÑOS SOCIO', 'persona': socio.nombre_completo, 'detalle': f"SOCIO: {socio.numero_socio or ''} - {socio.nombre_completo}"})
        if socio.fecha_nacimiento_esposa and socio.fecha_nacimiento_esposa.month == mes_actual_num:
            festividades.append({'dia': socio.fecha_nacimiento_esposa.day, 'tipo': 'CUMPLEAÑOS CONYUGE', 'persona': socio.nombre_esposa or 'CONYUGE', 'detalle': f"CONYUGE DE: {socio.nombre_completo}"})
        if socio.aniversario_matrimonio and socio.aniversario_matrimonio.month == mes_actual_num:
            festividades.append({'dia': socio.aniversario_matrimonio.day, 'tipo': 'ANIVERSARIO BODAS', 'persona': f"{socio.nombre_completo} Y {socio.nombre_esposa or ''}", 'detalle': "ANIVERSARIO MATRIMONIAL"})
        if socio.hijos:
            for hijo in socio.hijos:
                if hijo.fecha_nacimiento and hijo.fecha_nacimiento.month == mes_actual_num:
                    festividades.append({'dia': hijo.fecha_nacimiento.day, 'tipo': 'CUMPLE HIJO(A)', 'persona': hijo.nombre, 'detalle': f"HIJO(A) DE: {socio.nombre_completo}"})
    festividades = sorted(festividades, key=lambda x: x['dia'])
    usuarios_por_socio = {}
    try:
        for u in Usuario.query.all():
            if u.socio_id:
                usuarios_por_socio[u.socio_id] = u
            else:
                # Buscar por username = numero_socio
                s_match = next((s for s in lista_socios if s.numero_socio and s.numero_socio.strip().upper() == u.username), None)
                if s_match:
                    usuarios_por_socio[s_match.id] = u
    except:
        pass
    _u = Usuario.query.get(session.get('user_id')) if session.get('user_id') else None
    mi_socio_id = _u.socio_id if _u else None
    if not mi_socio_id and session.get('username'):
        _s = next((s for s in lista_socios if s.numero_socio and s.numero_socio.strip().upper() == session.get('username','').strip().upper()), None)
        mi_socio_id = _s.id if _s else None
    return render_template('socios.html', socios=lista_socios, festividades_mes=festividades, mes_actual_nombre=mes_actual_nombre, usuarios_por_socio=usuarios_por_socio, mi_socio_id=mi_socio_id)

@app.route('/socios/agregar', methods=['POST'])
def agregar_socio():
    # REGLA: crear socio nuevo solo ADMIN (no es dato personal propio)
    if 'user_id' not in session or session.get('rol') != 'ADMIN':
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
            flash(f'Error foto: {e}', 'warning')
    db.session.add(nuevo)
    db.session.flush()
    # CREAR USUARIO AUTOMATICO - numero_socio = username, sin contraseña
    try:
        if nuevo.numero_socio:
            uname = nuevo.numero_socio.strip().upper()
            if not Usuario.query.filter_by(username=uname).first():
                db.session.add(Usuario(username=uname, password_hash=None, rol='SOCIO', socio_id=nuevo.id, debe_crear_password=True))
    except Exception as e:
        print(f"Crear usuario socio: {e}")
    cargo_inicial = request.form.get('cargo_inicial')
    periodo_inicial = request.form.get('periodo_inicial') or '2026-2027'
    if cargo_inicial:
        db.session.add(HistorialCargo(socio_id=nuevo.id, cargo=cargo_inicial.upper(), periodo=periodo_inicial.upper(), es_actual=True))
    db.session.commit()
    flash('Socio agregado.', 'success')
    return redirect(url_for('gestion_socios'))

@app.route('/socios/editar/<int:socio_id>', methods=['POST'])
def editar_socio(socio_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    socio = Socio.query.get_or_404(socio_id)
    # REGLA DATOS PERSONALES: excepto ADMIN, solo puedes editar TUS datos
    if not es_mi_socio(socio):
        flash(f'Solo puedes editar tus datos personales. Este socio es {socio.nombre_completo}.', 'danger')
        return redirect(url_for('gestion_socios'))
    def parse_date(date_str):
        if date_str:
            try:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return None
        return None
    # Sin ser ADMIN no puede cambiar su numero_socio (es su usuario)
    if session.get('rol') == 'ADMIN':
        socio.numero_socio = to_upper(request.form.get('numero_socio')) or socio.numero_socio
    socio.nombre_completo = to_upper(request.form.get('nombre_completo')) or socio.nombre_completo
    socio.tipo_socio = to_upper(request.form.get('tipo_socio')) or socio.tipo_socio
    socio.telefono = to_upper(request.form.get('telefono')) or socio.telefono
    socio.correo = request.form.get('correo') or socio.correo
    socio.fecha_nacimiento = parse_date(request.form.get('fecha_nacimiento')) or socio.fecha_nacimiento
    foto_archivo = request.files.get('foto_archivo')
    if foto_archivo and foto_archivo.filename and allowed_file(foto_archivo.filename):
        contenido = foto_archivo.read()
        mime = foto_archivo.mimetype or 'image/jpeg'
        b64 = base64.b64encode(contenido).decode('utf-8')
        socio.foto_url = f"data:{mime};base64,{b64}"
    for hijo in list(socio.hijos):
        if request.form.get(f'hijo_eliminar_{hijo.id}') == '1':
            db.session.delete(hijo)
        else:
            nn = request.form.get(f'hijo_nombre_{hijo.id}')
            if nn:
                hijo.nombre = to_upper(nn)
                hijo.fecha_nacimiento = parse_date(request.form.get(f'hijo_fecha_{hijo.id}')) or hijo.fecha_nacimiento
    for i in range(1, 9):
        n_nombre = request.form.get(f'nuevo_hijo_nombre_{i}')
        n_fecha = request.form.get(f'nuevo_hijo_fecha_{i}')
        if n_nombre and n_nombre.strip():
            db.session.add(Hijo(socio_id=socio.id, nombre=to_upper(n_nombre), fecha_nacimiento=parse_date(n_fecha)))
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
            festividades.append({'fecha_str': f"{socio.fecha_nacimiento.day:02d}/{socio.fecha_nacimiento.month:02d}", 'tipo': 'CUMPLEAÑOS SOCIO', 'persona': socio.nombre_completo, 'detalle': f"SOCIO ID: {socio.numero_socio or socio.id}", 'dia': socio.fecha_nacimiento.day})
    festividades = sorted(festividades, key=lambda x: x['dia'])
    return render_template('cumpleanos.html', festividades=festividades, mes_actual=mes_actual_nombre)


@app.route('/gestion-rotaria')
def gestion_rotaria():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    tipo_filtro = request.args.get('tipo', 'TODOS')
    estado_filtro = request.args.get('estado', 'TODOS')
    
    query = DocumentoRotario.query
    if tipo_filtro != 'TODOS':
        query = query.filter_by(tipo=tipo_filtro)
    if estado_filtro != 'TODOS':
        query = query.filter_by(estado=estado_filtro)
    
    documentos = query.order_by(DocumentoRotario.fecha_documento.desc(), DocumentoRotario.id.desc()).all()
    
    tipos = ['ACTA','ACUERDO','PRESIDENCIA','SECRETARIA','FUNDACION','SERVICIOS','TESORERIA','MEMBRESIA','OTRO']
    
    total_actas = DocumentoRotario.query.filter_by(tipo='ACTA').count()
    total_acuerdos = DocumentoRotario.query.filter_by(tipo='ACUERDO').count()
    total_presidencia = DocumentoRotario.query.filter_by(tipo='PRESIDENCIA').count()
    total_secretaria = DocumentoRotario.query.filter_by(tipo='SECRETARIA').count()
    total_fundacion = DocumentoRotario.query.filter_by(tipo='FUNDACION').count()
    total_servicios = DocumentoRotario.query.filter_by(tipo='SERVICIOS').count()
    
    return render_template('gestion_rotaria.html',
                           documentos=documentos,
                           tipos=tipos,
                           tipo_filtro=tipo_filtro,
                           estado_filtro=estado_filtro,
                           total_actas=total_actas,
                           total_acuerdos=total_acuerdos,
                           total_presidencia=total_presidencia,
                           total_secretaria=total_secretaria,
                           total_fundacion=total_fundacion,
                           total_servicios=total_servicios)

@app.route('/gestion-rotaria/subir', methods=['POST'])
def subir_documento_rotario():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    tipo = request.form.get('tipo','ACTA').strip().upper()
    titulo = request.form.get('titulo','').strip().upper()
    descripcion = request.form.get('descripcion','').strip()
    estado = request.form.get('estado','VIGENTE').strip().upper()
    fecha_str = request.form.get('fecha_documento')
    try:
        fecha_doc = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else datetime.now().date()
    except:
        fecha_doc = datetime.now().date()
    # SEGUIMIENTO
    def _parse(d):
        try:
            return datetime.strptime(d, '%Y-%m-%d').date() if d else None
        except:
            return None
    tiene_fechas = request.form.get('tiene_fechas') == '1' or request.form.get('tiene_fechas') == 'on'
    fecha_inicio = _parse(request.form.get('fecha_inicio'))
    fecha_termino = _parse(request.form.get('fecha_termino'))
    responsable = request.form.get('responsable','').strip().upper() or None
    prioridad = request.form.get('prioridad','MEDIA').strip().upper()
    try:
        porcentaje_avance = int(request.form.get('porcentaje_avance') or 0)
    except:
        porcentaje_avance = 0
    # FECHA DE EJECUCION - nueva opcion
    tiene_fecha_ejecucion = request.form.get('tiene_fecha_ejecucion') == '1' or request.form.get('tiene_fecha_ejecucion') == 'on'
    fecha_ejecucion = _fecha_ejecucion_form() or _parse(request.form.get('fecha_ejecucion'))
    if fecha_ejecucion:
        tiene_fecha_ejecucion = True
    
    archivo_nombre = None
    archivo_b64 = None
    modo = request.form.get('modo', 'PDF')  # PDF o SISTEMA
    if 'archivo' in request.files:
        f = request.files['archivo']
        if f and f.filename and f.filename.lower().endswith('.pdf'):
            data = f.read()
            if len(data) <= 20 * 1024 * 1024:
                archivo_nombre = f.filename
                archivo_b64 = base64.b64encode(data).decode('utf-8')
    
    # Si modo es PDF, exigir archivo; si es SISTEMA, permitir sin PDF
    if modo == 'PDF' and not archivo_b64:
        flash('Debes subir un PDF en modo SUBIR PDF. Para crear sin PDF usa CREAR EN SISTEMA.', 'danger')
        return redirect(url_for('gestion_rotaria'))
    
    # Si es SISTEMA sin PDF, pon nombre generico
    if not archivo_b64:
        archivo_nombre = 'CREADO EN SISTEMA - SIN PDF'
    
    doc = DocumentoRotario(
        tipo=tipo,
        titulo=titulo,
        descripcion=descripcion,
        fecha_documento=fecha_doc,
        estado=estado,
        archivo_nombre=archivo_nombre,
        archivo_base64=archivo_b64,
        subido_por=session.get('username','SISTEMA'),
        tiene_fechas=tiene_fechas,
        fecha_inicio=fecha_inicio,
        fecha_termino=fecha_termino,
        responsable=responsable,
        prioridad=prioridad,
        porcentaje_avance=porcentaje_avance,
        tiene_fecha_ejecucion=tiene_fecha_ejecucion,
        fecha_ejecucion=fecha_ejecucion
    )
    db.session.add(doc)
    db.session.commit()
    flash(f'Documento {titulo} subido correctamente.', 'success')
    return redirect(url_for('gestion_rotaria', tipo=tipo))

@app.route('/gestion-rotaria/ver/<int:doc_id>')
def ver_documento_rotario(doc_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    doc = DocumentoRotario.query.get_or_404(doc_id)
    if not doc.archivo_base64:
        flash('Sin archivo.', 'warning')
        return redirect(url_for('gestion_rotaria'))
    try:
        pdf_bytes = base64.b64decode(doc.archivo_base64)
        from flask import Response
        return Response(pdf_bytes, mimetype='application/pdf', headers={'Content-Disposition': f'inline; filename={doc.archivo_nombre or "documento.pdf"}'})
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return redirect(url_for('gestion_rotaria'))

@app.route('/gestion-rotaria/descargar/<int:doc_id>')
def descargar_documento_rotario(doc_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    doc = DocumentoRotario.query.get_or_404(doc_id)
    if not doc.archivo_base64:
        flash('Sin archivo.', 'warning')
        return redirect(url_for('gestion_rotaria'))
    try:
        pdf_bytes = base64.b64decode(doc.archivo_base64)
        from flask import Response
        return Response(pdf_bytes, mimetype='application/pdf', headers={'Content-Disposition': f'attachment; filename={doc.archivo_nombre or "documento.pdf"}'})
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return redirect(url_for('gestion_rotaria'))

@app.route('/gestion-rotaria/eliminar/<int:doc_id>', methods=['POST'])
def eliminar_documento_rotario(doc_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    doc = DocumentoRotario.query.get_or_404(doc_id)
    # REGLA ERP BORRAR: solo PRESIDENTE y ADMIN (aunque el creador sea otro socio, no puede borrar)
    if session.get('rol') not in ['ADMIN', 'PRESIDENTE']:
        flash('Solo PRESIDENTE y ADMIN pueden borrar en ERP.', 'danger')
        return redirect(url_for('gestion_rotaria'))
    db.session.delete(doc)
    db.session.commit()
    flash(f'Documento {doc.titulo} eliminado.', 'warning')
    return redirect(url_for('gestion_rotaria'))

@app.route('/gestion-rotaria/editar/<int:doc_id>', methods=['POST'])
def editar_documento_rotario(doc_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    doc = DocumentoRotario.query.get_or_404(doc_id)
    # REGLA ERP EDITAR: solo el creador o ADMIN. PRESIDENTE no edita lo de otros, solo puede borrar.
    if doc.subido_por and doc.subido_por != session.get('username') and session.get('rol') != 'ADMIN':
        flash(f'Solo {doc.subido_por} (creador) o ADMIN puede editar este documento.', 'danger')
        return redirect(url_for('gestion_rotaria'))
    doc.tipo = request.form.get('tipo','ACTA').strip().upper()
    doc.titulo = request.form.get('titulo','').strip().upper()
    doc.descripcion = request.form.get('descripcion','').strip()
    doc.estado = request.form.get('estado','VIGENTE').strip().upper()
    fecha_str = request.form.get('fecha_documento')
    try:
        if fecha_str:
            doc.fecha_documento = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except:
        pass
    # SEGUIMIENTO + FECHA EJECUCION en editar
    def _parse2(d):
        try:
            return datetime.strptime(d, '%Y-%m-%d').date() if d else None
        except:
            return None
    doc.tiene_fechas = request.form.get('tiene_fechas') == '1' or request.form.get('tiene_fechas') == 'on'
    doc.fecha_inicio = _parse2(request.form.get('fecha_inicio'))
    doc.fecha_termino = _parse2(request.form.get('fecha_termino'))
    doc.responsable = request.form.get('responsable','').strip().upper() or None
    doc.prioridad = request.form.get('prioridad','MEDIA').strip().upper()
    try:
        doc.porcentaje_avance = int(request.form.get('porcentaje_avance') or doc.porcentaje_avance or 0)
    except:
        pass
    doc.tiene_fecha_ejecucion = request.form.get('tiene_fecha_ejecucion') == '1' or request.form.get('tiene_fecha_ejecucion') == 'on'
    doc.fecha_ejecucion = _fecha_ejecucion_form() or _parse2(request.form.get('fecha_ejecucion'))
    if doc.fecha_ejecucion:
        doc.tiene_fecha_ejecucion = True
    if 'archivo' in request.files:
        f = request.files['archivo']
        if f and f.filename and f.filename.lower().endswith('.pdf'):
            data = f.read()
            if data:
                doc.archivo_nombre = f.filename
                doc.archivo_base64 = base64.b64encode(data).decode('utf-8')
    db.session.commit()
    flash('Documento actualizado.', 'success')
    return redirect(url_for('gestion_rotaria'))

@app.route('/autoridades')
def gestion_autoridades():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    autoridades = AutoridadRotaria.query.order_by(AutoridadRotaria.nivel.asc()).all()
    return render_template('autoridades.html', autoridades=autoridades)

@app.route('/autoridades/guardar', methods=['POST'])
def guardar_autoridad():
    if 'user_id' not in session or session.get('rol') not in ['ADMIN', 'PRESIDENTE']:
        flash('No autorizado.', 'danger')
        return redirect(url_for('gestion_autoridades'))
    if request.form.get('nombre') and request.form.get('cargo'):
        db.session.add(AutoridadRotaria(nombre=to_upper(request.form.get('nombre')), cargo=to_upper(request.form.get('cargo')), nivel=to_upper(request.form.get('nivel')), correo=request.form.get('correo'), telefono=request.form.get('telefono')))
        db.session.commit()
    return redirect(url_for('gestion_autoridades'))

@app.route('/autoridades/eliminar/<int:id>', methods=['POST'])
def eliminar_autoridad(id):
    if 'user_id' not in session or session.get('rol') not in ['ADMIN', 'PRESIDENTE']:
        flash('Solo ADMIN o PRESIDENTE pueden borrar autoridades.', 'danger')
        return redirect(url_for('gestion_autoridades'))
    aut = AutoridadRotaria.query.get_or_404(id)
    db.session.delete(aut)
    db.session.commit()
    return redirect(url_for('gestion_autoridades'))

@app.route('/tesoreria')
def modulo_tesoreria():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # REGLA CORREGIDA: SOCIO no ve menu de tesoreria completo, solo estados de cuenta
    if solo_estado_cuenta():
        return redirect(url_for('estado_cuenta_mensual'))
    # Resumen financiero para menu
    total_cuotas = db.session.query(func.sum(PagoCuota.monto)).scalar() or 0
    total_gastos_admin = db.session.query(func.sum(Gasto.monto)).filter_by(centro_costo='ADMINISTRATIVO').scalar() or 0
    total_proyectos_ing = db.session.query(func.sum(EventoProyecto.monto_recaudado)).scalar() or 0
    total_gastos_proy = db.session.query(func.sum(Gasto.monto)).filter_by(centro_costo='PROYECTO').scalar() or 0
    proyectos = Proyecto.query.filter_by(activo=True).all()
    return render_template('tesoreria_menu.html', total_cuotas=total_cuotas, total_gastos_admin=total_gastos_admin, balance_cuotas=total_cuotas-total_gastos_admin, total_proyectos_ing=total_proyectos_ing, total_gastos_proy=total_gastos_proy, balance_proyectos=total_proyectos_ing-total_gastos_proy, proyectos=proyectos)

@app.route('/tesoreria/cuotas-sociales')
def cuotas_sociales():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if solo_estado_cuenta():
        return redirect(url_for('estado_cuenta_mensual'))
    socios = Socio.query.filter_by(es_activo=True).order_by(Socio.nombre_completo.asc()).all()
    config_teso = ConfiguracionTesoreria.query.first()
    saldo_inicial = config_teso.saldo_inicial if config_teso else 0.0
    total_recaudado = db.session.query(func.sum(PagoCuota.monto)).scalar() or 0.0
    total_ingresos_proyectos = db.session.query(func.sum(EventoProyecto.monto_recaudado)).scalar() or 0.0
    total_ingresos_extra = db.session.query(func.sum(IngresoExtraordinario.monto)).scalar() or 0.0
    total_gastos_admin = db.session.query(func.sum(Gasto.monto)).filter_by(centro_costo='ADMINISTRATIVO').scalar() or 0.0
    total_gastos_proy = db.session.query(func.sum(Gasto.monto)).filter_by(centro_costo='PROYECTO').scalar() or 0.0
    saldo_total_general = saldo_inicial + total_recaudado + total_ingresos_proyectos + total_ingresos_extra - total_gastos_admin - total_gastos_proy
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
    return render_template('tesoreria.html', socios=socios, meses=MESES_CONTROL, ultimo_pago=ultimo_pago, pagos_recibo=pagos_recibo, saldo_inicial=saldo_inicial, saldo_total_general=saldo_total_general, total_recaudado=total_recaudado, total_ingresos_proyectos=total_ingresos_proyectos, total_ingresos_extra=total_ingresos_extra, total_gastos_admin=total_gastos_admin, total_gastos_proy=total_gastos_proy)

@app.route('/tesoreria/actualizar-saldo-inicial', methods=['POST'])
def actualizar_saldo_inicial():
    if 'user_id' not in session or session.get('rol') not in ['ADMIN', 'TESORERO', 'PRESIDENTE']:
        flash('No autorizado.', 'danger')
        return redirect(url_for('menu_principal'))
    password = request.form.get('password')
    try:
        nuevo_saldo = float(request.form.get('saldo_inicial', 0.0))
    except:
        flash('Saldo invalido', 'danger')
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
        flash('Saldo actualizado!', 'success')
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
        flash(f'{len(pagos_creados_ids)} pago(s) registrado(s).', 'success')
        return redirect(url_for('cuotas_sociales', recibo_ids=','.join(pagos_creados_ids)))
    else:
        flash('Ya estaban pagados.', 'info')
        return redirect(url_for('cuotas_sociales'))

@app.route('/tesoreria/editar-pago/<int:pago_id>', methods=['POST'])
def editar_pago_cuota(pago_id):
    # REGLA TESORERIA: escribir/editar/borrar solo ADMIN/PRESIDENTE/TESORERO
    if 'user_id' not in session or not puede_tesoreria():
        flash('Solo ADMIN, PRESIDENTE o TESORERO pueden editar pagos.', 'danger')
        return redirect(url_for('cuotas_sociales'))
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
    if 'user_id' not in session:
        return redirect(url_for('login'))
    pago = PagoCuota.query.get_or_404(pago_id)
    # REGLA: SOCIO solo sus propios recibos
    if session.get('rol') not in ROLES_TESORERIA:
        _u = Usuario.query.get(session.get('user_id')) if session.get('user_id') else None
        _mi = _u.socio_id if _u and _u.socio_id else None
        if pago.socio_id != _mi:
            flash('Solo puedes ver TUS recibos.', 'danger')
            return redirect(url_for('estado_cuenta_mensual'))
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
    if 'user_id' not in session:
        return redirect(url_for('login'))
    socio = Socio.query.get_or_404(socio_id)
    # REGLA: SOCIO solo puede ver SU propio estado de cuenta, no el de otros
    if session.get('rol') not in ROLES_TESORERIA and not es_mi_socio(socio):
        flash('Solo puedes ver TU estado de cuenta.', 'danger')
        return redirect(url_for('estado_cuenta_mensual'))
    meses_es = {"January": "ENERO", "February": "FEBRERO", "March": "MARZO", "April": "ABRIL", "May": "MAYO", "June": "JUNIO", "July": "JULIO", "August": "AGOSTO", "September": "SEPTIEMBRE", "October": "OCTUBRE", "November": "NOVIEMBRE", "December": "DICIEMBRE"}
    dias_es = {"Monday": "LUNES", "Tuesday": "MARTES", "Wednesday": "MIÉRCOLES", "Thursday": "JUEVES", "Friday": "VIERNES", "Saturday": "SÁBADO", "Sunday": "DOMINGO"}
    ahora = datetime.now()
    fecha_actual_str = f"{dias_es.get(ahora.strftime('%A'), '')}, {ahora.day} DE {meses_es.get(ahora.strftime('%B'), '')} DE {ahora.year}"
    return render_template('estado_cuenta_pdf.html', socio=socio, meses=MESES_CONTROL, fecha_actual_str=fecha_actual_str)

# ==================== NUEVO MODULO GASTOS ====================
@app.route('/tesoreria/gastos')
def tesoreria_gastos():
    # REGLA CORREGIDA: gastos solo ADMIN/PRESIDENTE/TESORERO. SOCIO solo estados de cuenta.
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if solo_estado_cuenta():
        return redirect(url_for('estado_cuenta_mensual'))
    mes_filtro = request.args.get('mes', get_mes_anio_actual())
    gastos_mes = Gasto.query.filter_by(mes_anio=mes_filtro).order_by(Gasto.fecha.desc()).all()
    total_admin = sum([g.monto for g in gastos_mes if g.centro_costo == 'ADMINISTRATIVO'])
    total_proyecto = sum([g.monto for g in gastos_mes if g.centro_costo == 'PROYECTO'])
    proyectos = Proyecto.query.filter_by(activo=True).all()
    try:
        total_cuotas_mes = db.session.query(func.sum(PagoCuota.monto)).filter(func.upper(func.trim(PagoCuota.mes_anio)) == mes_filtro.strip().upper()).scalar() or 0
    except:
        total_cuotas_mes = 0
    meses_lista = []
    now = datetime.now()
    for i in range(18):
        m = now.month - i
        y = now.year
        while m <= 0:
            m += 12
            y -= 1
        meses_lista.append(f"{MESES_NOMBRES[m-1]} {y}")
    return render_template('tesoreria_gastos.html', gastos=gastos_mes, proyectos=proyectos, mes_actual=mes_filtro, meses_lista=meses_lista, total_admin=total_admin, total_proyecto=total_proyecto, total_cuotas_mes=total_cuotas_mes, balance_cuotas=total_cuotas_mes-total_admin)

@app.route('/tesoreria/gastos/nuevo', methods=['POST'])
def nuevo_gasto():
    if 'user_id' not in session or session.get('rol') not in ['ADMIN', 'TESORERO', 'PRESIDENTE']:
        return redirect(url_for('login'))
    fecha_str = request.form.get('fecha')
    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else datetime.now().date()
    mes_anio = f"{MESES_NOMBRES[fecha.month-1]} {fecha.year}"
    centro = request.form.get('centro_costo')
    proyecto_id = request.form.get('proyecto_id') if centro == 'PROYECTO' else None
    foto_b64 = None
    foto_archivo = request.files.get('foto_comprobante')
    if foto_archivo and foto_archivo.filename:
        try:
            contenido = foto_archivo.read()
            if len(contenido) > 0 and len(contenido) < 8*1024*1024:
                mime = foto_archivo.mimetype or 'image/jpeg'
                b64 = base64.b64encode(contenido).decode('utf-8')
                foto_b64 = f"data:{mime};base64,{b64}"
        except Exception as e:
            print(f"Error foto comprobante: {e}")
    gasto = Gasto(
        fecha=fecha,
        mes_anio=mes_anio,
        concepto=request.form.get('concepto').upper(),
        monto=float(request.form.get('monto')),
        centro_costo=centro,
        proyecto_id=int(proyecto_id) if proyecto_id else None,
        comprobante=request.form.get('comprobante'),
        foto_comprobante=foto_b64,
        creado_por=session.get('username','TESORERIA'),
        notas=request.form.get('notas')
    )
    db.session.add(gasto)
    db.session.commit()
    flash(f'Gasto registrado: {gasto.concepto} - ${gasto.monto:,.2f} con comprobante', 'success')
    return redirect(url_for('tesoreria_gastos', mes=mes_anio))

@app.route('/tesoreria/gastos/eliminar/<int:gasto_id>', methods=['POST'])
def eliminar_gasto(gasto_id):
    if 'user_id' not in session or not puede_tesoreria():
        flash('Solo ADMIN, PRESIDENTE o TESORERO pueden borrar gastos.', 'danger')
        return redirect(url_for('tesoreria_gastos'))
    gasto = Gasto.query.get_or_404(gasto_id)
    mes = gasto.mes_anio
    db.session.delete(gasto)
    db.session.commit()
    flash('Gasto eliminado.', 'warning')
    return redirect(url_for('tesoreria_gastos', mes=mes))

# ==================== MODULO PROYECTOS ====================
@app.route('/tesoreria/proyectos')
def tesoreria_proyectos():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if solo_estado_cuenta():
        return redirect(url_for('estado_cuenta_mensual'))
    proyectos = Proyecto.query.order_by(Proyecto.fecha_creacion.desc()).all()
    for p in proyectos:
        total_rec = sum([e.monto_recaudado for e in p.eventos]) if p.eventos else 0
        total_gas = sum([g.monto for g in p.gastos]) if p.gastos else 0
        p.total_recaudado_calc = total_rec
        p.total_gastado_calc = total_gas
        p.balance_calc = total_rec - total_gas
        total_meta = sum([e.monto_meta for e in p.eventos]) if p.eventos else 0
        p.total_meta_calc = total_meta
        p.porcentaje_calc = (total_rec / total_meta * 100) if total_meta > 0 else 0
    return render_template('tesoreria_proyectos.html', proyectos=proyectos)

@app.route('/tesoreria/proyecto/nuevo', methods=['POST'])
def nuevo_proyecto():
    if 'user_id' not in session or session.get('rol') not in ['ADMIN', 'TESORERO', 'PRESIDENTE']:
        return redirect(url_for('login'))
    nombre = request.form.get('nombre').upper()
    proyecto = Proyecto(nombre=nombre, descripcion=request.form.get('descripcion'))
    db.session.add(proyecto)
    db.session.commit()
    flash(f'Proyecto creado: {nombre}', 'success')
    return redirect(url_for('tesoreria_proyectos'))

@app.route('/tesoreria/proyecto/<int:proyecto_id>')
def ver_proyecto(proyecto_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if solo_estado_cuenta():
        return redirect(url_for('estado_cuenta_mensual'))
    proyecto = Proyecto.query.get_or_404(proyecto_id)
    eventos = EventoProyecto.query.filter_by(proyecto_id=proyecto_id).order_by(EventoProyecto.fecha_evento.desc()).all()
    gastos = Gasto.query.filter_by(proyecto_id=proyecto_id).order_by(Gasto.fecha.desc()).all()
    total_recaudado = sum([e.monto_recaudado for e in eventos])
    total_meta = sum([e.monto_meta for e in eventos])
    total_gastos = sum([g.monto for g in gastos])
    return render_template('tesoreria_proyecto_detalle.html', proyecto=proyecto, eventos=eventos, gastos=gastos, total_recaudado=total_recaudado, total_meta=total_meta, total_gastos=total_gastos, balance=total_recaudado-total_gastos)

@app.route('/tesoreria/proyecto/<int:proyecto_id>/evento/nuevo', methods=['POST'])
def nuevo_evento_proyecto(proyecto_id):
    if 'user_id' not in session or session.get('rol') not in ['ADMIN', 'TESORERO', 'PRESIDENTE']:
        return redirect(url_for('login'))
    proyecto = Proyecto.query.get_or_404(proyecto_id)
    evento = EventoProyecto(
        proyecto_id=proyecto_id,
        nombre=request.form.get('nombre').upper(),
        descripcion=request.form.get('descripcion'),
        monto_meta=float(request.form.get('monto_meta')),
        monto_recaudado=float(request.form.get('monto_recaudado') or 0),
        fecha_evento=datetime.strptime(request.form.get('fecha_evento'), '%Y-%m-%d').date() if request.form.get('fecha_evento') else None,
        detalle_recaudado=request.form.get('detalle_recaudado')
    )
    db.session.add(evento)
    db.session.commit()
    flash(f'Evento creado: {evento.nombre} - Meta ${evento.monto_meta:,.2f}', 'success')
    return redirect(url_for('ver_proyecto', proyecto_id=proyecto_id))

@app.route('/tesoreria/evento/<int:evento_id>/actualizar', methods=['POST'])
def actualizar_evento(evento_id):
    if 'user_id' not in session or not puede_tesoreria():
        flash('Solo ADMIN, PRESIDENTE o TESORERO pueden editar eventos.', 'danger')
        return redirect(url_for('tesoreria_proyectos'))
    evento = EventoProyecto.query.get_or_404(evento_id)
    evento.monto_recaudado = float(request.form.get('monto_recaudado'))
    evento.detalle_recaudado = request.form.get('detalle_recaudado')
    evento.nombre = request.form.get('nombre', evento.nombre).upper()
    db.session.commit()
    flash(f'Evento actualizado: {evento.nombre} - ${evento.monto_recaudado:,.2f}', 'success')
    return redirect(url_for('ver_proyecto', proyecto_id=evento.proyecto_id))

@app.route('/tesoreria/evento/<int:evento_id>/eliminar', methods=['POST'])
def eliminar_evento(evento_id):
    if 'user_id' not in session or not puede_tesoreria():
        flash('Solo ADMIN, PRESIDENTE o TESORERO pueden borrar eventos.', 'danger')
        return redirect(url_for('tesoreria_proyectos'))
    evento = EventoProyecto.query.get_or_404(evento_id)
    pid = evento.proyecto_id
    db.session.delete(evento)
    db.session.commit()
    flash('Evento eliminado.', 'warning')
    return redirect(url_for('ver_proyecto', proyecto_id=pid))


# ==================== ESTADO DE CUENTA MENSUAL ====================
@app.route('/tesoreria/estado-cuenta-mensual')
def estado_cuenta_mensual():
    # REGLA: TODOS pueden ver estado de cuenta mensual y meses anteriores
    if 'user_id' not in session:
        return redirect(url_for('login'))
    mes_filtro = request.args.get('mes', get_mes_anio_actual())
    # meses lista
    meses_lista = []
    now = datetime.now()
    for i in range(18):
        m = now.month - i
        y = now.year
        while m <= 0:
            m += 12
            y -= 1
        meses_lista.append(f"{MESES_NOMBRES[m-1]} {y}")

    config = ConfiguracionTesoreria.query.first()
    saldo_inicial = config.saldo_inicial if config else 0.0

    # CUOTAS MES
    pagos_cuotas = PagoCuota.query.filter(func.upper(func.trim(PagoCuota.mes_anio)) == mes_filtro.strip().upper()).all()
    total_cuotas_mes = sum([p.monto for p in pagos_cuotas]) if pagos_cuotas else 0

    # GASTOS MES
    gastos_admin = Gasto.query.filter_by(mes_anio=mes_filtro, centro_costo='ADMINISTRATIVO').order_by(Gasto.fecha.desc()).all()
    gastos_proy = Gasto.query.filter_by(mes_anio=mes_filtro, centro_costo='PROYECTO').order_by(Gasto.fecha.desc()).all()
    total_gastos_admin_mes = sum([g.monto for g in gastos_admin]) if gastos_admin else 0
    total_gastos_proy_mes = sum([g.monto for g in gastos_proy]) if gastos_proy else 0

    # INGRESOS PROYECTOS MES
    try:
        mes_num = MESES_NOMBRES.index(mes_filtro.split()[0]) + 1
        anio_num = int(mes_filtro.split()[1])
        eventos_mes = EventoProyecto.query.filter(func.extract('month', EventoProyecto.fecha_evento) == mes_num, func.extract('year', EventoProyecto.fecha_evento) == anio_num).all()
    except:
        eventos_mes = []

    total_ingresos_proyectos_mes = sum([e.monto_recaudado for e in eventos_mes]) if eventos_mes else 0

    # INGRESOS EXTRAORDINARIOS / DONACIONES MES - NUEVO
    ingresos_extra_mes = IngresoExtraordinario.query.filter_by(mes_anio=mes_filtro).order_by(IngresoExtraordinario.fecha.desc()).all()
    total_ingresos_extra_mes = sum([i.monto for i in ingresos_extra_mes]) if ingresos_extra_mes else 0

    # Si no hay eventos filtrados por fecha, intenta buscar por mes_anio no existe en eventos, entonces usa 0
    # Pero para que veas datos, si no hay eventos en ese mes, total_ingresos_proyectos_mes = 0, puedes ajustar luego

    total_ingresos = saldo_inicial + total_cuotas_mes + total_ingresos_proyectos_mes + total_ingresos_extra_mes
    total_egresos = total_gastos_admin_mes + total_gastos_proy_mes
    balance_final = total_cuotas_mes + total_ingresos_proyectos_mes + total_ingresos_extra_mes - total_egresos
    balance_acumulado = saldo_inicial + total_cuotas_mes + total_ingresos_proyectos_mes + total_ingresos_extra_mes - total_gastos_admin_mes - total_gastos_proy_mes

    # Historicos totales
    total_cuotas_historico = db.session.query(func.sum(PagoCuota.monto)).scalar() or 0
    total_gastos_admin_hist = db.session.query(func.sum(Gasto.monto)).filter_by(centro_costo='ADMINISTRATIVO').scalar() or 0
    total_gastos_proy_hist = db.session.query(func.sum(Gasto.monto)).filter_by(centro_costo='PROYECTO').scalar() or 0
    total_ingresos_proy_hist = db.session.query(func.sum(EventoProyecto.monto_recaudado)).scalar() or 0
    total_ingresos_extra_hist = db.session.query(func.sum(IngresoExtraordinario.monto)).scalar() or 0

    saldo_cuotas = total_cuotas_mes - total_gastos_admin_mes
    saldo_proyectos = total_ingresos_proyectos_mes - total_gastos_proy_mes
    saldo_extra = total_ingresos_extra_mes

    return render_template('estado_cuenta_mensual.html',
                           mes_actual=mes_filtro,
                           meses_lista=meses_lista,
                           saldo_inicial=saldo_inicial,
                           pagos_cuotas=pagos_cuotas,
                           total_cuotas_mes=total_cuotas_mes,
                           num_pagos_cuotas=len(pagos_cuotas),
                           gastos_admin=gastos_admin,
                           gastos_proy=gastos_proy,
                           total_gastos_admin_mes=total_gastos_admin_mes,
                           total_gastos_proy_mes=total_gastos_proy_mes,
                           num_gastos_admin=len(gastos_admin),
                           num_gastos_proy=len(gastos_proy),
                           eventos_mes=eventos_mes,
                           total_ingresos_proyectos_mes=total_ingresos_proyectos_mes,
                           num_eventos_mes=len(eventos_mes),
                           ingresos_extra_mes=ingresos_extra_mes,
                           total_ingresos_extra_mes=total_ingresos_extra_mes,
                           total_ingresos=total_ingresos,
                           total_egresos=total_egresos,
                           balance_final=balance_final,
                           balance_acumulado=balance_acumulado,
                           total_cuotas_historico=total_cuotas_historico,
                           total_gastos_admin_hist=total_gastos_admin_hist,
                           total_gastos_proy_hist=total_gastos_proy_hist,
                           total_ingresos_proy_hist=total_ingresos_proy_hist,
                           total_ingresos_extra_hist=total_ingresos_extra_hist,
                           saldo_cuotas=saldo_cuotas,
                           saldo_proyectos=saldo_proyectos,
                           saldo_extra=saldo_extra)

@app.route('/tesoreria/estado-cuenta-pdf-mensual')
def estado_cuenta_pdf_mensual():
    # REGLA: es estado de cuenta mensual, TODOS pueden verlo (incluido SOCIO)
    if 'user_id' not in session:
        return redirect(url_for('login'))
    mes_filtro = request.args.get('mes', get_mes_anio_actual())
    config = ConfiguracionTesoreria.query.first()
    saldo_inicial = config.saldo_inicial if config else 0.0
    pagos_cuotas = PagoCuota.query.filter(func.upper(func.trim(PagoCuota.mes_anio)) == mes_filtro.strip().upper()).all()
    total_cuotas_mes = sum([p.monto for p in pagos_cuotas]) if pagos_cuotas else 0
    gastos_admin = Gasto.query.filter_by(mes_anio=mes_filtro, centro_costo='ADMINISTRATIVO').all()
    gastos_proy = Gasto.query.filter_by(mes_anio=mes_filtro, centro_costo='PROYECTO').all()
    total_gastos_admin_mes = sum([g.monto for g in gastos_admin]) if gastos_admin else 0
    total_gastos_proy_mes = sum([g.monto for g in gastos_proy]) if gastos_proy else 0
    try:
        mes_num = MESES_NOMBRES.index(mes_filtro.split()[0]) + 1
        anio_num = int(mes_filtro.split()[1])
        eventos_mes = EventoProyecto.query.filter(func.extract('month', EventoProyecto.fecha_evento) == mes_num, func.extract('year', EventoProyecto.fecha_evento) == anio_num).all()
    except:
        eventos_mes = []
    total_ingresos_proyectos_mes = sum([e.monto_recaudado for e in eventos_mes]) if eventos_mes else 0
    # INGRESOS EXTRAORDINARIOS / DONACIONES
    ingresos_extra_mes = IngresoExtraordinario.query.filter_by(mes_anio=mes_filtro).order_by(IngresoExtraordinario.fecha.desc()).all()
    total_ingresos_extra_mes = sum([i.monto for i in ingresos_extra_mes]) if ingresos_extra_mes else 0
    total_ingresos = saldo_inicial + total_cuotas_mes + total_ingresos_proyectos_mes + total_ingresos_extra_mes
    total_egresos = total_gastos_admin_mes + total_gastos_proy_mes
    balance_final = total_cuotas_mes + total_ingresos_proyectos_mes + total_ingresos_extra_mes - total_egresos
    balance_acumulado = saldo_inicial + balance_final
    fecha_gen = datetime.now().strftime('%d/%m/%Y %H:%M')
    return render_template('estado_cuenta_mensual_pdf.html',
                           mes_actual=mes_filtro,
                           saldo_inicial=saldo_inicial,
                           pagos_cuotas=pagos_cuotas,
                           total_cuotas_mes=total_cuotas_mes,
                           num_pagos_cuotas=len(pagos_cuotas),
                           gastos_admin=gastos_admin,
                           gastos_proy=gastos_proy,
                           total_gastos_admin_mes=total_gastos_admin_mes,
                           total_gastos_proy_mes=total_gastos_proy_mes,
                           eventos_mes=eventos_mes,
                           total_ingresos_proyectos_mes=total_ingresos_proyectos_mes,
                           ingresos_extra_mes=ingresos_extra_mes,
                           total_ingresos_extra_mes=total_ingresos_extra_mes,
                           total_ingresos=total_ingresos,
                           total_egresos=total_egresos,
                           balance_final=balance_final,
                           balance_acumulado=balance_acumulado,
                           fecha_generacion=fecha_gen)


@app.route('/tesoreria/recaudacion-mensual')
def recaudacion_mensual():
    # REGLA CORREGIDA: recaudacion NO es estado de cuenta, solo ADMIN/PRESIDENTE/TESORERO
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if solo_estado_cuenta():
        return redirect(url_for('estado_cuenta_mensual'))
    total_socios = Socio.query.filter_by(es_activo=True).count()
    if total_socios == 0:
        total_socios = 12
    cuota_mensual = 500
    esperado_por_mes = total_socios * cuota_mensual
    anios_disponibles = sorted(list(set([m.split()[-1] for m in MESES_CONTROL if m.split()[-1].isdigit()])))
    if not anios_disponibles:
        anios_disponibles = ["2025", "2026"]
    anio_filtro = request.args.get('anio', None)
    def calcular_meses(lista_meses):
        resultado = []
        total_recibido = 0
        for mes in lista_meses:
            pagos_mes = PagoCuota.query.filter(func.upper(func.trim(PagoCuota.mes_anio)) == mes.strip().upper()).all()
            recibido = sum([p.monto for p in pagos_mes]) if pagos_mes else 0
            esperado = esperado_por_mes
            diferencia = esperado - recibido
            porcentaje = (recibido / esperado * 100) if esperado > 0 else 0
            tipo = "ESTADISTICO" if "2025" in mes else "CAJA"
            resultado.append({'mes': mes, 'recibido': recibido, 'esperado': esperado, 'diferencia': diferencia, 'porcentaje': porcentaje, 'num_pagos': len(pagos_mes), 'tipo': tipo})
            total_recibido += recibido
        return resultado, total_recibido
    if anio_filtro and anio_filtro in anios_disponibles:
        meses_filtrados = [m for m in MESES_CONTROL if anio_filtro in m]
        meses_data, total_filtrado = calcular_meses(meses_filtrados)
        meses_2025 = []; meses_2026 = []; meses_2027 = []
        if anio_filtro == "2025": meses_2025 = meses_data
        elif anio_filtro == "2026": meses_2026 = meses_data
        else: meses_2027 = meses_data
        meses_2025_all, total_2025_all = calcular_meses([m for m in MESES_CONTROL if "2025" in m])
        meses_2026_all, total_2026_all = calcular_meses([m for m in MESES_CONTROL if "2026" in m])
        meses_2027_all, total_2027_all = calcular_meses([m for m in MESES_CONTROL if "2027" in m])
    else:
        meses_2025, total_2025 = calcular_meses([m for m in MESES_CONTROL if "2025" in m])
        meses_2026, total_2026 = calcular_meses([m for m in MESES_CONTROL if "2026" in m])
        meses_2027, total_2027 = calcular_meses([m for m in MESES_CONTROL if "2027" in m])
        meses_2025_all = meses_2025; meses_2026_all = meses_2026; meses_2027_all = meses_2027
        total_2025_all = total_2025; total_2026_all = total_2026; total_2027_all = total_2027
        anio_filtro = "TODOS"
    esperado_2025 = len([m for m in MESES_CONTROL if "2025" in m]) * esperado_por_mes
    esperado_2026 = len([m for m in MESES_CONTROL if "2026" in m]) * esperado_por_mes
    esperado_2027 = len([m for m in MESES_CONTROL if "2027" in m]) * esperado_por_mes if any("2027" in m for m in MESES_CONTROL) else 0
    porc_2025 = (total_2025_all / esperado_2025 * 100) if esperado_2025 else 0
    porc_2026 = (total_2026_all / esperado_2026 * 100) if esperado_2026 else 0
    porc_2027 = (total_2027_all / esperado_2027 * 100) if esperado_2027 else 0
    comparacion_anual = []
    for anio in anios_disponibles:
        lista = [m for m in MESES_CONTROL if anio in m]
        datos, total = calcular_meses(lista)
        esperado = len(lista) * esperado_por_mes
        porc = (total / esperado * 100) if esperado else 0
        tipo = "ESTADISTICO - NO VA A CAJA" if anio == "2025" else "DINERO EN CAJA"
        comparacion_anual.append({'anio': anio, 'total_recibido': total, 'esperado': esperado, 'porcentaje': porc, 'meses': len(lista), 'tipo': tipo})
    return render_template('recaudacion_mensual.html',
                           total_socios=total_socios,
                           meses_2025=meses_2025,
                           meses_2026=meses_2026,
                           meses_2027=meses_2027,
                           total_2025=total_2025_all,
                           total_2026=total_2026_all,
                           total_2027=total_2027_all,
                           esperado_2025=esperado_2025,
                           esperado_2026=esperado_2026,
                           esperado_2027=esperado_2027,
                           porc_2025=porc_2025,
                           porc_2026=porc_2026,
                           porc_2027=porc_2027,
                           anios_disponibles=anios_disponibles,
                           anio_filtro=anio_filtro,
                           comparacion_anual=comparacion_anual,
                           cuota_mensual=cuota_mensual)


@app.route('/tesoreria/ingresos-extraordinarios')
def ingresos_extraordinarios():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if solo_estado_cuenta():
        return redirect(url_for('estado_cuenta_mensual'))
    mes_filtro = request.args.get('mes', get_mes_anio_actual())
    meses_lista = []
    now = datetime.now()
    for i in range(18):
        m = now.month - i
        y = now.year
        while m <= 0:
            m += 12
            y -= 1
        meses_lista.append(f"{MESES_NOMBRES[m-1]} {y}")
    
    ingresos = IngresoExtraordinario.query.filter_by(mes_anio=mes_filtro).order_by(IngresoExtraordinario.fecha.desc()).all()
    total_mes = sum([i.monto for i in ingresos]) if ingresos else 0
    
    # Totales historicos
    total_historico = db.session.query(func.sum(IngresoExtraordinario.monto)).scalar() or 0
    total_donaciones = db.session.query(func.sum(IngresoExtraordinario.monto)).filter_by(tipo='DONACION').scalar() or 0
    total_patrocinios = db.session.query(func.sum(IngresoExtraordinario.monto)).filter_by(tipo='PATROCINIO').scalar() or 0
    
    # Para saldo
    config = ConfiguracionTesoreria.query.first()
    saldo_inicial = config.saldo_inicial if config else 0.0
    
    return render_template('ingresos_extraordinarios.html',
                           ingresos=ingresos,
                           mes_actual=mes_filtro,
                           meses_lista=meses_lista,
                           total_mes=total_mes,
                           total_historico=total_historico,
                           total_donaciones=total_donaciones,
                           total_patrocinios=total_patrocinios,
                           saldo_inicial=saldo_inicial)

@app.route('/tesoreria/ingresos-extraordinarios/nuevo', methods=['POST'])
def nuevo_ingreso_extraordinario():
    if 'user_id' not in session or session.get('rol') not in ['ADMIN', 'TESORERO', 'PRESIDENTE']:
        flash('No autorizado.', 'danger')
        return redirect(url_for('menu_principal'))
    mes_anio = request.form.get('mes_anio', get_mes_anio_actual()).strip().upper()
    concepto = to_upper(request.form.get('concepto'))
    tipo = request.form.get('tipo', 'DONACION').strip().upper()
    origen = to_upper(request.form.get('origen'))
    referencia = to_upper(request.form.get('referencia'))
    notas = request.form.get('notas')
    try:
        monto = float(request.form.get('monto', 0))
    except:
        flash('Monto invalido.', 'danger')
        return redirect(url_for('ingresos_extraordinarios', mes=mes_anio))
    
    fecha_str = request.form.get('fecha')
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else datetime.now().date()
    except:
        fecha = datetime.now().date()
    
    # Comprobante base64 opcional
    comprobante_nombre = None
    comprobante_b64 = None
    if 'comprobante' in request.files:
        file = request.files['comprobante']
        if file and file.filename:
            if file.filename.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg')):
                contenido = file.read()
                if len(contenido) <= 15 * 1024 * 1024:
                    comprobante_nombre = file.filename
                    comprobante_b64 = base64.b64encode(contenido).decode('utf-8')
    
    ingreso = IngresoExtraordinario(
        fecha=fecha,
        mes_anio=mes_anio,
        concepto=concepto,
        monto=monto,
        tipo=tipo,
        origen=origen,
        referencia=referencia,
        comprobante_nombre=comprobante_nombre,
        comprobante_base64=comprobante_b64,
        registrado_por=session.get('username', 'SISTEMA'),
        notas=notas
    )
    db.session.add(ingreso)
    db.session.commit()
    flash(f'Ingreso extraordinario {concepto} - ${monto:.2f} registrado.', 'success')
    return redirect(url_for('ingresos_extraordinarios', mes=mes_anio))

@app.route('/tesoreria/ingresos-extraordinarios/eliminar/<int:ingreso_id>', methods=['POST'])
def eliminar_ingreso_extraordinario(ingreso_id):
    if 'user_id' not in session or not puede_tesoreria():
        flash('Solo ADMIN, PRESIDENTE o TESORERO puede eliminar.', 'danger')
        return redirect(url_for('ingresos_extraordinarios'))
    ingreso = IngresoExtraordinario.query.get_or_404(ingreso_id)
    mes = ingreso.mes_anio
    db.session.delete(ingreso)
    db.session.commit()
    flash(f'Ingreso {ingreso.concepto} eliminado.', 'warning')
    return redirect(url_for('ingresos_extraordinarios', mes=mes))

@app.route('/tesoreria/ingresos-extraordinarios/ver/<int:ingreso_id>')
def ver_comprobante_ingreso(ingreso_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if solo_estado_cuenta():
        return redirect(url_for('estado_cuenta_mensual'))
    ingreso = IngresoExtraordinario.query.get_or_404(ingreso_id)
    if not ingreso.comprobante_base64:
        flash('Sin comprobante.', 'warning')
        return redirect(url_for('ingresos_extraordinarios', mes=ingreso.mes_anio))
    try:
        file_bytes = base64.b64decode(ingreso.comprobante_base64)
        from flask import Response
        mimetype = 'application/pdf' if ingreso.comprobante_nombre and ingreso.comprobante_nombre.lower().endswith('.pdf') else 'image/jpeg'
        return Response(file_bytes, mimetype=mimetype, headers={'Content-Disposition': f'inline; filename={ingreso.comprobante_nombre or "comprobante.pdf"}'})
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return redirect(url_for('ingresos_extraordinarios', mes=ingreso.mes_anio))

@app.route('/logout')

def logout():
    session.clear()
    return redirect(url_for('index_publico'))

if __name__ == '__main__':
    app.run(debug=True)


