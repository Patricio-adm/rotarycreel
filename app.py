from sqlalchemy import func
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

MESES_NOMBRES = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]

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
    foto_comprobante = db.Column(db.Text, nullable=True)  # FOTO base64 comprobante
    creado_por = db.Column(db.String(100), nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    notas = db.Column(db.Text, nullable=True)

with app.app_context():
    db.create_all()
    try:
        PagoCuota.__table__.create(db.engine, checkfirst=True)
        ConfiguracionTesoreria.__table__.create(db.engine, checkfirst=True)
        Proyecto.__table__.create(db.engine, checkfirst=True)
        EventoProyecto.__table__.create(db.engine, checkfirst=True)
        Gasto.__table__.create(db.engine, checkfirst=True)
    except Exception as e:
        print(f"Info tablas: {e}")
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
    # Crear PROYECTO BOMBERA si no existe
    if not Proyecto.query.filter_by(nombre='PROYECTO BOMBERA').first():
        p = Proyecto(nombre='PROYECTO BOMBERA', descripcion='Proyecto activo recaudacion para bomberos Creel', activo=True)
        db.session.add(p)
        db.session.commit()

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
    return render_template('socios.html', socios=lista_socios)

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
            flash(f'Error foto: {e}', 'warning')
    db.session.add(nuevo)
    db.session.flush()
    cargo_inicial = request.form.get('cargo_inicial')
    periodo_inicial = request.form.get('periodo_inicial') or '2026-2027'
    if cargo_inicial:
        db.session.add(HistorialCargo(socio_id=nuevo.id, cargo=cargo_inicial.upper(), periodo=periodo_inicial.upper(), es_actual=True))
    db.session.commit()
    flash('Socio agregado.', 'success')
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
    for i in range(1, 4):
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
    aut = AutoridadRotaria.query.get_or_404(id)
    db.session.delete(aut)
    db.session.commit()
    return redirect(url_for('gestion_autoridades'))

@app.route('/tesoreria')
def modulo_tesoreria():
    if 'user_id' not in session:
        return redirect(url_for('login'))
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
    socios = Socio.query.filter_by(es_activo=True).order_by(Socio.nombre_completo.asc()).all()
    config_teso = ConfiguracionTesoreria.query.first()
    saldo_inicial = config_teso.saldo_inicial if config_teso else 0.0
    total_recaudado = PagoCuota.query.filter(PagoCuota.mes_anio.in_(MESES_CONTROL)).with_entities(func.sum(PagoCuota.monto)).scalar() or 0.0
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

# ==================== NUEVO MODULO GASTOS ====================
@app.route('/tesoreria/gastos')
def tesoreria_gastos():
    if 'user_id' not in session or session.get('rol') not in ['ADMIN', 'TESORERO', 'PRESIDENTE']:
        return redirect(url_for('login'))
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
    # Foto comprobante - subir/tomar foto
    foto_b64 = None
    foto_archivo = request.files.get('foto_comprobante')
    if foto_archivo and foto_archivo.filename:
        try:
            contenido = foto_archivo.read()
            if len(contenido) > 0 and len(contenido) < 8*1024*1024:  # max 8MB
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
    evento = EventoProyecto.query.get_or_404(evento_id)
    evento.monto_recaudado = float(request.form.get('monto_recaudado'))
    evento.detalle_recaudado = request.form.get('detalle_recaudado')
    evento.nombre = request.form.get('nombre', evento.nombre).upper()
    db.session.commit()
    flash(f'Evento actualizado: {evento.nombre} - ${evento.monto_recaudado:,.2f}', 'success')
    return redirect(url_for('ver_proyecto', proyecto_id=evento.proyecto_id))

@app.route('/tesoreria/evento/<int:evento_id>/eliminar', methods=['POST'])
def eliminar_evento(evento_id):
    evento = EventoProyecto.query.get_or_404(evento_id)
    pid = evento.proyecto_id
    db.session.delete(evento)
    db.session.commit()
    flash('Evento eliminado.', 'warning')
    return redirect(url_for('ver_proyecto', proyecto_id=pid))

@app.route('/tesoreria/recaudacion-mensual')
def recaudacion_mensual():
    if 'user_id' not in session or session.get('rol') not in ['ADMIN', 'TESORERO', 'PRESIDENTE']:
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

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index_publico'))

if __name__ == '__main__':
    app.run(debug=True)
