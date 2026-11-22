from sqlalchemy import func
from flask import Flask, render_template, render_template_string, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
import base64
from datetime import datetime, date
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
    # HISTORICO - Club fundado 23 NOV 2024
    fecha_fundacion = db.Column(db.Date, default=date(2024, 11, 23))
    saldo_inicial_cuotas = db.Column(db.Float, default=0.0)
    saldo_inicial_proyectos = db.Column(db.Float, default=0.0)
    nota_saldos_iniciales = db.Column(db.Text, nullable=True)

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
    # MIGRACION HISTORICO: si la tabla configuracion_tesoreria ya existia, agregarle las columnas nuevas (create_all NO las agrega sola)
    try:
        from sqlalchemy import text as _sa_text
        for _col, _tipo in [('fecha_fundacion', 'DATE'), ('saldo_inicial_cuotas', 'DOUBLE PRECISION'), ('saldo_inicial_proyectos', 'DOUBLE PRECISION'), ('nota_saldos_iniciales', 'TEXT')]:
            try:
                db.session.execute(_sa_text(f"ALTER TABLE configuracion_tesoreria ADD COLUMN IF NOT EXISTS {_col} {_tipo}"))
            except Exception as _e:
                print(f"Migracion {_col}: {_e}")
        # La fila que ya existia quedo con NULL -> convertirla a 0 / 23 NOV 2024 para que no truene la suma
        db.session.execute(_sa_text("UPDATE configuracion_tesoreria SET saldo_inicial = COALESCE(saldo_inicial, 0), saldo_inicial_cuotas = COALESCE(saldo_inicial_cuotas, saldo_inicial, 0), saldo_inicial_proyectos = COALESCE(saldo_inicial_proyectos, 0), fecha_fundacion = COALESCE(fecha_fundacion, DATE '2024-11-23')"))
        db.session.commit()
    except Exception as _e:
        print(f"Migracion historico: {_e}")
        try: db.session.rollback()
        except: pass
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


def get_mi_socio():
    """Socio del usuario logueado (por socio_id o por username = numero_socio). None si no tiene socio vinculado."""
    try:
        u = Usuario.query.get(session.get('user_id')) if session.get('user_id') else None
        if u and u.socio_id:
            s = Socio.query.get(u.socio_id)
            if s:
                return s
        if session.get('username'):
            s = Socio.query.filter(func.lower(Socio.numero_socio) == session.get('username','').strip().lower()).first()
            if s:
                return s
    except Exception:
        pass
    return None

def puede_tesoreria():
    return session.get('rol') in ROLES_TESORERIA

def solo_estado_cuenta():
    """Si es SOCIO (no ADMIN/PRESIDENTE/TESORERO), no puede ver tesoreria completa, solo estados de cuenta."""
    if session.get('rol') not in ROLES_TESORERIA:
        flash('Como SOCIO solo puedes ver ESTADOS DE CUENTA (mensual y meses anteriores).', 'warning')
        return True
    return False



def _fecha_ejecucion_form():
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
            btn = f'<form method="POST" action="/admin/usuarios/cambiar/{u.id}" style="display:inline;"><input type="password" id="pass{u.id}" name="nueva_password" placeholder="Nueva (8+1+1)" style="width:110px;font-size:11px;" required><button type="button" onclick="var i=document.getElementById(\'pass{u.id}\'); i.type=(i.type==\'password\'?\'text\':\'password\'); this.textContent=(i.type==\'text\'?\'🙈\':\'👁️\');">👁️</button><button class="btn btn-warning btn-sm fw-bold">✏️ CAMBIAR</button></form> <form method="POST" action="/admin/usuarios/reset/{u.id}" style="display:inline;"><button class="btn btn-danger btn-sm fw-bold">🗑️ BORRAR</button></form>'
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
            if ev.fecha_ejecucion and ev.fecha_ejecucion.month == mes_actual_num and ev.fecha_ejecucion.year == datetime.now().year:
                _vistos.add(ev.id)
                festividades.append({'dia': ev.fecha_ejecucion.day, 'tipo': '📅 EVENTO / FECHA DE EJECUCION', 'persona': ev.titulo, 'detalle': f"{ev.tipo} - EJECUCION: {ev.fecha_ejecucion.strftime('%d/%m/%Y')} - {ev.descripcion[:80] if ev.descripcion else ''}", 'es_evento': True, 'doc_id': ev.id})
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
    # FAMILIA / DOMICILIO / EMERGENCIA (repuesto: el form los mandaba pero no se guardaban)
    socio.ciudad = to_upper(request.form.get('ciudad')) or socio.ciudad
    socio.calle_numero = to_upper(request.form.get('calle_numero')) or socio.calle_numero
    socio.colonia = to_upper(request.form.get('colonia')) or socio.colonia
    socio.codigo_postal = to_upper(request.form.get('codigo_postal')) or socio.codigo_postal
    socio.estado = to_upper(request.form.get('estado')) or socio.estado
    socio.estado_civil = to_upper(request.form.get('estado_civil')) or socio.estado_civil
    socio.telefono_emergencia = to_upper(request.form.get('telefono_emergencia')) or socio.telefono_emergencia
    socio.nombre_esposa = to_upper(request.form.get('nombre_esposa')) or socio.nombre_esposa
    socio.fecha_nacimiento_esposa = parse_date(request.form.get('fecha_nacimiento_esposa')) or socio.fecha_nacimiento_esposa
    socio.aniversario_matrimonio = parse_date(request.form.get('aniversario_matrimonio')) or socio.aniversario_matrimonio
    socio.telefono_esposa = to_upper(request.form.get('telefono_esposa')) or socio.telefono_esposa
    # CARGOS - actualizar existentes
    for cargo in list(socio.cargos):
        if request.form.get(f'cargo_eliminar_{cargo.id}') == '1':
            db.session.delete(cargo)
        else:
            nc = request.form.get(f'cargo_nombre_{cargo.id}')
            if nc and nc.strip():
                cargo.cargo = nc.strip().upper()
                cargo.periodo = request.form.get(f'cargo_periodo_{cargo.id}') or cargo.periodo
                cargo.es_actual = request.form.get(f'cargo_actual_{cargo.id}') == '1'
    # CARGOS - nuevos (hasta 10)
    for i in range(1, 11):
        n_cargo = request.form.get(f'nuevo_cargo_nombre_{i}')
        n_periodo = request.form.get(f'nuevo_cargo_periodo_{i}')
        if n_cargo and n_cargo.strip() and n_periodo:
            db.session.add(HistorialCargo(socio_id=socio.id, cargo=n_cargo.strip().upper(), periodo=n_periodo.strip(), es_actual=(request.form.get(f'nuevo_cargo_actual_{i}') == '1')))
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

    # ============ CALENDARIO ERP - mes por mes ============
    import calendar as _cal
    _mes_param = request.args.get('mes', '')
    try:
        _anio_cal, _mes_cal = map(int, _mes_param.split('-')) if _mes_param else (datetime.now().year, datetime.now().month)
        if not (1 <= _mes_cal <= 12): raise ValueError()
    except Exception:
        _anio_cal, _mes_cal = datetime.now().year, datetime.now().month
    _mes_ant = (_anio_cal, _mes_cal - 1) if _mes_cal > 1 else (_anio_cal - 1, 12)
    _mes_sig = (_anio_cal, _mes_cal + 1) if _mes_cal < 12 else (_anio_cal + 1, 1)
    _cal_eventos = {}  # 'YYYY-MM-DD' -> [doc]
    for _d in documentos:
        _fechas = []
        if _d.fecha_ejecucion:
            _fechas = [_d.fecha_ejecucion]
        elif _d.fecha_inicio and _d.fecha_termino:
            _cur, _fin = _d.fecha_inicio, _d.fecha_termino
            _n = 0
            while _cur <= _fin and _n < 62:
                _fechas.append(_cur); _cur += timedelta(days=1); _n += 1
        elif _d.fecha_inicio:
            _fechas = [_d.fecha_inicio]
        elif _d.fecha_termino:
            _fechas = [_d.fecha_termino]
        elif _d.fecha_documento:
            _fechas = [_d.fecha_documento]
        for _f in _fechas:
            _cal_eventos.setdefault(_f.strftime('%Y-%m-%d'), []).append(_d)
    _cal_semanas = _cal.monthcalendar(_anio_cal, _mes_cal)
    _meses_es_cal = ['ENERO','FEBRERO','MARZO','ABRIL','MAYO','JUNIO','JULIO','AGOSTO','SEPTIEMBRE','OCTUBRE','NOVIEMBRE','DICIEMBRE']

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
                           total_servicios=total_servicios,
                           cal_anio=_anio_cal, cal_mes=_mes_cal, cal_mes_nombre=_meses_es_cal[_mes_cal-1],
                           cal_mes_param=f"{_anio_cal:04d}-{_mes_cal:02d}",
                           cal_mes_ant=f"{_mes_ant[0]:04d}-{_mes_ant[1]:02d}", cal_mes_sig=f"{_mes_sig[0]:04d}-{_mes_sig[1]:02d}",
                           cal_semanas=_cal_semanas, cal_eventos=_cal_eventos, hoy_iso=datetime.now().strftime('%Y-%m-%d'))

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

@app.route('/tesoreria/mis-estados')
@app.route('/tesoreria/mis_estados')
def tesoreria_mis_estados():
    """HUB para SOCIO: dos botones - ESTADO PERSONAL y ESTADO CLUB. Tesoreria/ADMIN tambien pueden entrar."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    mi_socio = get_mi_socio()
    # Para ADMIN / TESORERO / PRESIDENTE, mi_socio puede ser None (cuenta fija) - el hub igual sirve, eligen socio en Personal
    return render_template('tesoreria_socio.html', mi_socio=mi_socio, mes_actual=get_mes_anio_actual())

@app.route('/tesoreria/estado-personal')
def tesoreria_estado_personal():
    """Atajo: mi estado personal sin tener que pasar el ID. SOCIO solo el suyo."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    mi_socio = get_mi_socio()
    if not mi_socio:
        flash('No tienes socio vinculado. Pide a ADMIN que vincule tu usuario con tu ficha de socio.', 'warning')
        return redirect(url_for('tesoreria_mis_estados'))
    return redirect(url_for('estado_cuenta_pdf', socio_id=mi_socio.id))

@app.route('/tesoreria')
def modulo_tesoreria():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # SOCIO: no ve menu de tesoreria completo, va al HUB con 2 botones: PERSONAL y CLUB
    if session.get('rol') not in ROLES_TESORERIA:
        return redirect(url_for('tesoreria_mis_estados'))
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
    if session.get('rol') not in ROLES_TESORERIA:
        return redirect(url_for('tesoreria_mis_estados'))
    socios = Socio.query.filter_by(es_activo=True).order_by(Socio.nombre_completo.asc()).all()
    config_teso = ConfiguracionTesoreria.query.first()
    saldo_inicial = float(config_teso.saldo_inicial or 0.0) if config_teso else 0.0
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


@app.route('/tesoreria/pagos')
def tesoreria_pagos():
    """Lista de TODOS los pagos de cuotas con EDITAR y BORRAR. Solo ADMIN/PRESIDENTE/TESORERO."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if not puede_tesoreria():
        flash('Solo ADMIN, PRESIDENTE o TESORERO pueden corregir pagos.', 'danger')
        return redirect(url_for('tesoreria_mis_estados'))
    q = request.args.get('q', '').strip()
    mes_f = request.args.get('mes', '').strip().upper()
    pagos_q = PagoCuota.query.join(Socio, PagoCuota.socio_id == Socio.id)
    if q:
        pagos_q = pagos_q.filter(Socio.nombre_completo.ilike(f'%{q}%'))
    if mes_f:
        pagos_q = pagos_q.filter(func.upper(func.trim(PagoCuota.mes_anio)) == mes_f)
    pagos = pagos_q.order_by(PagoCuota.fecha_pago.desc(), PagoCuota.id.desc()).limit(500).all()
    socios = Socio.query.filter_by(es_activo=True).order_by(Socio.nombre_completo.asc()).all()
    return render_template('tesoreria_pagos.html', pagos=pagos, socios=socios, meses=MESES_CONTROL, q=q, mes_f=mes_f)

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
    # Fecha real del pago (permite cargar historico desde 23 NOV 2024)
    _fp = request.form.get('fecha_pago')
    try:
        fecha_pago = datetime.strptime(_fp, '%Y-%m-%d').date() if _fp else datetime.now().date()
    except:
        fecha_pago = datetime.now().date()
    if fecha_pago < date(2024, 11, 23):
        flash('La fecha no puede ser antes de la fundacion del Club (23 NOV 2024).', 'danger')
        return redirect(url_for('cuotas_sociales'))
    pagos_creados_ids = []
    for m in meses_pagados:
        mes_limpio = m.strip().upper()
        existente = PagoCuota.query.filter_by(socio_id=socio_id, mes_anio=mes_limpio).first()
        if not existente:
            pago = PagoCuota(socio_id=socio_id, mes_anio=mes_limpio, monto=500.0, metodo_pago=metodo, referencia=referencia, fecha_pago=fecha_pago)
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
        db.session.commit()
        flash(f'Pago eliminado: {pago.mes_anio} - ${pago.monto:.2f}.', 'warning')
        return redirect(request.form.get('volver') or url_for('cuotas_sociales'))
    # EDITAR: mes, socio, monto, metodo, referencia y fecha
    nuevo_mes = (request.form.get('mes_anio') or pago.mes_anio).strip().upper()
    try:
        nuevo_socio_id = int(request.form.get('socio_id') or pago.socio_id)
    except:
        nuevo_socio_id = pago.socio_id
    # Control de duplicado: mismo socio + mismo mes en otro pago
    dup = PagoCuota.query.filter(PagoCuota.socio_id == nuevo_socio_id, func.upper(func.trim(PagoCuota.mes_anio)) == nuevo_mes, PagoCuota.id != pago.id).first()
    if dup:
        flash(f'Ya existe un pago de ese socio en {nuevo_mes}. No se puede duplicar. Cambia el mes o borra el duplicado.', 'danger')
        return redirect(request.form.get('volver') or url_for('cuotas_sociales'))
    try:
        pago.monto = float(request.form.get('monto', 500.0))
    except:
        pago.monto = 500.0
    pago.socio_id = nuevo_socio_id
    pago.mes_anio = nuevo_mes
    pago.metodo_pago = to_upper(request.form.get('metodo_pago'))
    pago.referencia = to_upper(request.form.get('referencia'))
    _fp = request.form.get('fecha_pago')
    if _fp:
        try:
            pago.fecha_pago = datetime.strptime(_fp, '%Y-%m-%d').date()
        except:
            pass
    db.session.commit()
    flash(f'Pago corregido: {pago.mes_anio} - ${pago.monto:.2f}.', 'success')
    return redirect(request.form.get('volver') or url_for('cuotas_sociales'))

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
    if session.get('rol') not in ROLES_TESORERIA:
        return redirect(url_for('tesoreria_mis_estados'))
    mes_filtro = request.args.get('mes', get_mes_anio_actual())
    gastos_mes = Gasto.query.filter_by(mes_anio=mes_filtro).order_by(Gasto.fecha.desc()).all()
    total_admin = sum([g.monto for g in gastos_mes if g.centro_costo == 'ADMINISTRATIVO'])
    total_proyecto = sum([g.monto for g in gastos_mes if g.centro_costo == 'PROYECTO'])
    proyectos = Proyecto.query.filter_by(activo=True).all()
    try:
        total_cuotas_mes = db.session.query(func.sum(PagoCuota.monto)).filter(func.upper(func.trim(PagoCuota.mes_anio)) == mes_filtro.strip().upper()).scalar() or 0
    except:
        total_cuotas_mes = 0
    # HISTORICO: meses desde la fundacion (NOV 2024) hasta hoy
    meses_lista = []
    _y, _m = 2024, 11
    _now = datetime.now()
    while (_y, _m) <= (_now.year, _now.month):
        meses_lista.append(f"{MESES_NOMBRES[_m-1]} {_y}")
        _m += 1
        if _m > 12:
            _m = 1; _y += 1
    meses_lista = list(reversed(meses_lista))
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
    # HISTORICO: meses desde la fundacion (NOV 2024) hasta hoy
    meses_lista = []
    _y, _m = 2024, 11
    _now = datetime.now()
    while (_y, _m) <= (_now.year, _now.month):
        meses_lista.append(f"{MESES_NOMBRES[_m-1]} {_y}")
        _m += 1
        if _m > 12:
            _m = 1; _y += 1
    meses_lista = list(reversed(meses_lista))

    config = ConfiguracionTesoreria.query.first()
    saldo_inicial = float(config.saldo_inicial or 0.0) if config else 0.0
    mi_socio = get_mi_socio()

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
                           saldo_extra=saldo_extra, mi_socio=mi_socio)

@app.route('/tesoreria/estado-cuenta-pdf-mensual')
def estado_cuenta_pdf_mensual():
    # REGLA: es estado de cuenta mensual, TODOS pueden verlo (incluido SOCIO)
    if 'user_id' not in session:
        return redirect(url_for('login'))
    mes_filtro = request.args.get('mes', get_mes_anio_actual())
    config = ConfiguracionTesoreria.query.first()
    saldo_inicial = float(config.saldo_inicial or 0.0) if config else 0.0
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
    if 'user_id' not in session:
        return redirect(url_for('login'))
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
    # HISTORICO: meses desde la fundacion (NOV 2024) hasta hoy
    meses_lista = []
    _y, _m = 2024, 11
    _now = datetime.now()
    while (_y, _m) <= (_now.year, _now.month):
        meses_lista.append(f"{MESES_NOMBRES[_m-1]} {_y}")
        _m += 1
        if _m > 12:
            _m = 1; _y += 1
    meses_lista = list(reversed(meses_lista))
    
    ingresos = IngresoExtraordinario.query.filter_by(mes_anio=mes_filtro).order_by(IngresoExtraordinario.fecha.desc()).all()
    total_mes = sum([i.monto for i in ingresos]) if ingresos else 0
    
    # Totales historicos
    total_historico = db.session.query(func.sum(IngresoExtraordinario.monto)).scalar() or 0
    total_donaciones = db.session.query(func.sum(IngresoExtraordinario.monto)).filter_by(tipo='DONACION').scalar() or 0
    total_patrocinios = db.session.query(func.sum(IngresoExtraordinario.monto)).filter_by(tipo='PATROCINIO').scalar() or 0
    
    # Para saldo
    config = ConfiguracionTesoreria.query.first()
    saldo_inicial = float(config.saldo_inicial or 0.0) if config else 0.0
    
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


@app.route('/_version')
def _version():
    """DIAGNOSTICO: visita /_version en Render. Si sale Not Found, Render NO esta corriendo este app.py."""
    rutas = sorted([str(r) for r in app.url_map.iter_rules() if 'tesoreria' in str(r)])
    return {'version': 'APP_PY_CON_MIS_ESTADOS_2026', 'mis_estados': '/tesoreria/mis-estados' in rutas, 'rutas_tesoreria': rutas}


# ================= HISTORICO TESORERIA - DESDE 23 NOV 2024 =================
@app.route('/tesoreria/historico')
def tesoreria_historico():
    """Vista unificada historica: saldos iniciales + ingresos + egresos + cuotas, desde la fundacion."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if not puede_tesoreria():
        return redirect(url_for('tesoreria_mis_estados'))
    config = ConfiguracionTesoreria.query.first()
    # FIX None: la fila vieja quedo con NULL en las columnas nuevas -> float(None) truena
    def _f(v, d=0.0):
        try: return float(v) if v is not None else float(d)
        except: return float(d)
    si_cuotas = _f(getattr(config, 'saldo_inicial_cuotas', None), _f(getattr(config, 'saldo_inicial', 0.0)) if config else 0.0)
    si_proy = _f(getattr(config, 'saldo_inicial_proyectos', 0.0)) if config else 0.0
    fecha_fund = getattr(config, 'fecha_fundacion', date(2024, 11, 23)) if config else date(2024, 11, 23)
    # Filtros
    desde = request.args.get('desde', '2024-11-23')
    hasta = request.args.get('hasta', datetime.now().strftime('%Y-%m-%d'))
    centro_f = request.args.get('centro', '')
    try:
        f_desde = datetime.strptime(desde, '%Y-%m-%d').date()
        f_hasta = datetime.strptime(hasta, '%Y-%m-%d').date()
    except:
        f_desde, f_hasta = date(2024, 11, 23), datetime.now().date()
    # Ingresos extra + Gastos en rango
    ingresos = IngresoExtraordinario.query.filter(IngresoExtraordinario.fecha >= f_desde, IngresoExtraordinario.fecha <= f_hasta).order_by(IngresoExtraordinario.fecha.desc()).all()
    gastos_q = Gasto.query.filter(Gasto.fecha >= f_desde, Gasto.fecha <= f_hasta)
    if centro_f:
        gastos_q = gastos_q.filter_by(centro_costo=centro_f)
    gastos = gastos_q.order_by(Gasto.fecha.desc()).all()
    # Cuotas en rango (por fecha_pago)
    cuotas = PagoCuota.query.filter(PagoCuota.fecha_pago >= f_desde, PagoCuota.fecha_pago <= f_hasta).order_by(PagoCuota.fecha_pago.desc()).all()
    total_ingresos = sum(_f(i.monto) for i in ingresos)
    total_gastos = sum(_f(g.monto) for g in gastos)
    total_gastos_admin = sum(_f(g.monto) for g in gastos if g.centro_costo == 'ADMINISTRATIVO')
    total_gastos_proy = sum(_f(g.monto) for g in gastos if g.centro_costo == 'PROYECTO')
    total_cuotas = sum(_f(p.monto) for p in cuotas)
    saldo_historico = si_cuotas + si_proy + total_cuotas + total_ingresos - total_gastos
    saldo_cuotas = si_cuotas + total_cuotas - total_gastos_admin
    # Proyectos: ingresos de eventos + SI proyectos - gastos proyecto (aprox, ingresos de eventos van en EventoProyecto)
    total_eventos_proy = db.session.query(func.sum(EventoProyecto.monto_recaudado)).scalar() or 0.0
    saldo_proyectos = si_proy + total_eventos_proy - total_gastos_proy
    proyectos = Proyecto.query.filter_by(activo=True).order_by(Proyecto.nombre.asc()).all()
    # Progreso por mes: para ir viendo que meses del libro ya estan capturados
    progreso = []
    _y, _m = 2024, 11
    _now = datetime.now()
    while (_y, _m) <= (_now.year, _now.month):
        _mes = f"{MESES_NOMBRES[_m-1]} {_y}"
        _n_g = Gasto.query.filter_by(mes_anio=_mes).count()
        _n_i = IngresoExtraordinario.query.filter_by(mes_anio=_mes).count()
        _n_c = PagoCuota.query.filter(func.upper(func.trim(PagoCuota.mes_anio)) == _mes).count()
        progreso.append({'mes': _mes, 'gastos': _n_g, 'ingresos': _n_i, 'cuotas': _n_c, 'total': _n_g + _n_i + _n_c})
        _m += 1
        if _m > 12: _m = 1; _y += 1
    progreso = list(reversed(progreso))
    return render_template('tesoreria_historico.html', progreso=progreso, config=config, si_cuotas=si_cuotas, si_proy=si_proy, fecha_fund=fecha_fund,
        ingresos=ingresos, gastos=gastos, cuotas=cuotas, proyectos=proyectos,
        total_ingresos=total_ingresos, total_gastos=total_gastos, total_gastos_admin=total_gastos_admin, total_gastos_proy=total_gastos_proy,
        total_cuotas=total_cuotas, saldo_historico=saldo_historico, saldo_cuotas=saldo_cuotas, saldo_proyectos=saldo_proyectos,
        total_eventos_proy=total_eventos_proy, desde=desde, hasta=hasta, centro_f=centro_f)

@app.route('/tesoreria/historico/nuevo', methods=['POST'])
def tesoreria_historico_nuevo():
    """Cargar UN movimiento historico con detalle: INGRESO o EGRESO, con fecha desde 23 NOV 2024."""
    if 'user_id' not in session or not puede_tesoreria():
        flash('Solo ADMIN, PRESIDENTE o TESORERO pueden cargar historico.', 'danger')
        return redirect(url_for('tesoreria_historico'))
    tipo_mov = request.form.get('tipo_mov', 'EGRESO').strip().upper()  # INGRESO / EGRESO
    fecha_str = request.form.get('fecha')
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else datetime.now().date()
    except:
        flash('Fecha invalida.', 'danger'); return redirect(url_for('tesoreria_historico'))
    if fecha < date(2024, 11, 23):
        flash('La fecha no puede ser antes de la fundacion (23 NOV 2024).', 'danger'); return redirect(url_for('tesoreria_historico'))
    if fecha > datetime.now().date():
        flash('La fecha no puede ser futura.', 'danger'); return redirect(url_for('tesoreria_historico'))
    concepto = to_upper(request.form.get('concepto'))
    try:
        monto = float(request.form.get('monto', 0))
    except:
        monto = 0
    if not concepto or monto <= 0:
        flash('Falta concepto o monto.', 'danger'); return redirect(url_for('tesoreria_historico'))
    mes_anio = f"{MESES_NOMBRES[fecha.month-1]} {fecha.year}"
    centro = request.form.get('centro_costo', 'ADMINISTRATIVO')
    proyecto_id = request.form.get('proyecto_id') if centro == 'PROYECTO' else None
    if proyecto_id:
        try: proyecto_id = int(proyecto_id)
        except: proyecto_id = None
    origen = to_upper(request.form.get('origen'))
    referencia = to_upper(request.form.get('referencia'))
    notas = request.form.get('notas')
    user = Usuario.query.get(session['user_id'])
    quien = user.nombre if user and hasattr(user, 'nombre') else (user.username if user else 'TESORERIA')
    if tipo_mov == 'INGRESO':
        tipo_ing = request.form.get('tipo_ingreso', 'DONACION').strip().upper()
        ing = IngresoExtraordinario(fecha=fecha, mes_anio=mes_anio, concepto=concepto, monto=monto, tipo=tipo_ing, origen=origen, referencia=referencia, notas=notas, registrado_por=quien)
        db.session.add(ing)
        db.session.commit()
        flash(f'Ingreso historico guardado: {concepto} - ${monto:,.2f} ({fecha.strftime("%d/%m/%Y")}).', 'success')
    else:
        # Foto comprobante opcional
        foto_b64 = None
        f = request.files.get('foto_comprobante')
        if f and f.filename:
            try:
                contenido = f.read()
                if 0 < len(contenido) < 8*1024*1024:
                    foto_b64 = f"data:{f.mimetype or 'image/jpeg'};base64,{base64.b64encode(contenido).decode('utf-8')}"
            except: pass
        g = Gasto(fecha=fecha, mes_anio=mes_anio, concepto=concepto, monto=monto, centro_costo=centro, proyecto_id=proyecto_id, comprobante=referencia, foto_comprobante=foto_b64, creado_por=quien, notas=notas)
        db.session.add(g)
        db.session.commit()
        flash(f'Egreso historico guardado: {concepto} - ${monto:,.2f} ({fecha.strftime("%d/%m/%Y")}).', 'success')
    return redirect(url_for('tesoreria_historico', desde=request.form.get('desde') or '2024-11-23', hasta=request.form.get('hasta') or datetime.now().strftime('%Y-%m-%d')))

@app.route('/tesoreria/historico/saldos-iniciales', methods=['POST'])
def tesoreria_saldos_iniciales():
    """Guardar saldos iniciales al 23 NOV 2024: cuotas + proyectos, con nota y password."""
    if 'user_id' not in session or not puede_tesoreria():
        flash('Solo ADMIN, PRESIDENTE o TESORERO.', 'danger'); return redirect(url_for('tesoreria_historico'))
    user = Usuario.query.get(session['user_id'])
    if not user or not check_password_hash(user.password_hash, request.form.get('password') or ''):
        flash('Contraseña incorrecta.', 'danger'); return redirect(url_for('tesoreria_historico'))
    try:
        si_cuotas = float(request.form.get('saldo_inicial_cuotas', 0) or 0)
        si_proy = float(request.form.get('saldo_inicial_proyectos', 0) or 0)
    except:
        flash('Monto invalido.', 'danger'); return redirect(url_for('tesoreria_historico'))
    config = ConfiguracionTesoreria.query.first()
    if not config:
        config = ConfiguracionTesoreria(saldo_inicial=si_cuotas, saldo_inicial_cuotas=si_cuotas, saldo_inicial_proyectos=si_proy)
        db.session.add(config)
    else:
        config.saldo_inicial = si_cuotas
        config.saldo_inicial_cuotas = si_cuotas
        config.saldo_inicial_proyectos = si_proy
        config.fecha_fundacion = date(2024, 11, 23)
    config.nota_saldos_iniciales = request.form.get('nota_saldos')
    config.fecha_actualizacion = datetime.now().date()
    db.session.commit()
    flash(f'Saldos iniciales guardados al 23 NOV 2024: Cuotas ${si_cuotas:,.2f} + Proyectos ${si_proy:,.2f}.', 'success')
    return redirect(url_for('tesoreria_historico'))



@app.route('/tesoreria/historico/masivo', methods=['POST'])
def tesoreria_historico_masivo():
    """Carga masiva desde el libro: pega renglones, uno por movimiento.
    Formato por renglon: FECHA | INGRESO/EGRESO | CONCEPTO | MONTO | CENTRO | PROYECTO | ORIGEN | REFERENCIA
    Fecha acepta 2024-11-25 o 25/11/2024. Monto acepta 1500, 1,500.00 o $1500."""
    if 'user_id' not in session or not puede_tesoreria():
        flash('Solo ADMIN, PRESIDENTE o TESORERO.', 'danger'); return redirect(url_for('tesoreria_historico'))
    texto = request.form.get('texto_masivo', '') or ''
    user = Usuario.query.get(session['user_id'])
    quien = user.nombre if user and hasattr(user, 'nombre') else (user.username if user else 'TESORERIA')
    guardados, errores = 0, []
    proyectos = {pr.nombre.strip().upper(): pr for pr in Proyecto.query.all()}
    for n, linea in enumerate(texto.splitlines(), 1):
        linea = linea.strip()
        if not linea or linea.startswith('#'):
            continue
        partes = [x.strip() for x in linea.split('|')]
        if len(partes) < 4:
            errores.append(f'Renglon {n}: le faltan campos (fecha | tipo | concepto | monto).')
            continue
        fecha_str, tipo_mov, concepto, monto_str = partes[0], partes[1].upper(), partes[2], partes[3]
        centro = (partes[4].upper() if len(partes) > 4 and partes[4] else 'ADMINISTRATIVO')
        nombre_proy = (partes[5] if len(partes) > 5 else '')
        origen = (partes[6] if len(partes) > 6 else '')
        referencia = (partes[7] if len(partes) > 7 else '')
        # Fecha
        fecha = None
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
            try: fecha = datetime.strptime(fecha_str, fmt).date(); break
            except: pass
        if not fecha:
            errores.append(f'Renglon {n}: fecha "{fecha_str}" no se entiende. Usa 2024-11-25 o 25/11/2024.'); continue
        if fecha < date(2024, 11, 23) or fecha > datetime.now().date():
            errores.append(f'Renglon {n}: fecha fuera de rango (23 NOV 2024 a hoy).'); continue
        try: monto = float(monto_str.replace('$', '').replace(',', '').strip())
        except: errores.append(f'Renglon {n}: monto "{monto_str}" no es numero.'); continue
        if monto <= 0:
            errores.append(f'Renglon {n}: monto debe ser mayor a 0.'); continue
        mes_anio = f"{MESES_NOMBRES[fecha.month-1]} {fecha.year}"
        if tipo_mov.startswith('ING'):
            ing = IngresoExtraordinario(fecha=fecha, mes_anio=mes_anio, concepto=to_upper(concepto), monto=monto, tipo='OTRO', origen=to_upper(origen), referencia=to_upper(referencia), registrado_por=quien)
            db.session.add(ing); guardados += 1
        elif tipo_mov.startswith('EGR'):
            pid = None
            if centro == 'PROYECTO' and nombre_proy:
                pr = proyectos.get(nombre_proy.strip().upper())
                pid = pr.id if pr else None
                if not pid: errores.append(f'Renglon {n}: proyecto "{nombre_proy}" no existe, se guardo sin proyecto.')
            g = Gasto(fecha=fecha, mes_anio=mes_anio, concepto=to_upper(concepto), monto=monto, centro_costo=centro if centro in ('ADMINISTRATIVO', 'PROYECTO') else 'ADMINISTRATIVO', proyecto_id=pid, comprobante=to_upper(referencia), creado_por=quien, notas=to_upper(origen))
            db.session.add(g); guardados += 1
        else:
            errores.append(f'Renglon {n}: tipo "{tipo_mov}" debe ser INGRESO o EGRESO.'); continue
    db.session.commit()
    if guardados:
        flash(f'Carga masiva: {guardados} movimiento(s) guardado(s) del libro.', 'success')
    for e in errores[:10]:
        flash(e, 'warning')
    if len(errores) > 10:
        flash(f'... y {len(errores)-10} renglones mas con error.', 'warning')
    if guardados == 0 and not errores:
        flash('No pegaste ningun renglon.', 'warning')
    return redirect(url_for('tesoreria_historico'))


if __name__ == '__main__':
    app.run(debug=True)


