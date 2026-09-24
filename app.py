from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
import base64
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'clave_secreta_rotary_creel_2026'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def to_upper(val):
    if val and isinstance(val, str):
        cleaned = val.strip().upper()
        return cleaned if cleaned else None
    return None

# Forzar el uso del driver psycopg2 para evitar errores de dependencias en Render
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
        print(f"Info tablas tesorería: {e}")

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

@app.route('/menu')
def menu_principal():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('menu.html')

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
        telefono_emergencia=to_upper(request.form.get('telefono_emergencia')),
        es_activo=True
    )

    try:
        file = request.files.get('foto_archivo')
        if file and file.filename != '':
            if allowed_file(file.filename):
                file_bytes = file.read()
                if file_bytes:
                    encoded_img = base64.b64encode(file_bytes).decode('utf-8')
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    mime_type = "image/jpeg" if ext in ['jpg', 'jpeg'] else f"image/{ext}"
                    nuevo.foto_url = f"data:{mime_type};base64,{encoded_img}"
    except Exception as e:
        print(f"Error procesando imagen: {e}")

    db.session.add(nuevo)
    db.session.flush()

    cargo_inicial = request.form.get('cargo_inicial')
    periodo_inicial = request.form.get('periodo_inicial')
    if cargo_inicial and periodo_inicial:
        db.session.add(HistorialCargo(socio_id=nuevo.id, cargo=to_upper(cargo_inicial), periodo=to_upper(periodo_inicial), es_actual=True))

    db.session.commit()
    flash('¡Socio registrado exitosamente!', 'success')
    return redirect(url_for('gestion_socios'))

@app.route('/socios/editar/<int:id>', methods=['POST'])
def editar_socio(id):
    if 'user_id' not in session or session.get('rol') not in ['ADMIN', 'TESORERO', 'PRESIDENTE']:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('gestion_socios'))

    socio = Socio.query.get_or_404(id)
    socio.numero_socio = to_upper(request.form.get('numero_socio'))
    socio.nombre_completo = to_upper(request.form.get('nombre_completo'))
    socio.telefono = to_upper(request.form.get('telefono'))
    socio.correo = request.form.get('correo')
    socio.tipo_socio = to_upper(request.form.get('tipo_socio')) or 'ACTIVO'
    socio.calle_numero = to_upper(request.form.get('calle_numero'))
    socio.colonia = to_upper(request.form.get('colonia'))
    socio.codigo_postal = to_upper(request.form.get('codigo_postal'))
    socio.ciudad = to_upper(request.form.get('ciudad'))
    socio.estado = to_upper(request.form.get('estado'))
    socio.estado_civil = to_upper(request.form.get('estado_civil'))
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

    socio.fecha_nacimiento = parse_date(request.form.get('fecha_nacimiento'))
    socio.fecha_nacimiento_esposa = parse_date(request.form.get('fecha_nacimiento_esposa'))
    socio.aniversario_matrimonio = parse_date(request.form.get('aniversario_matrimonio'))
    
    for hijo in socio.hijos:
        prefix = f"hijo_{hijo.id}_"
        if request.form.get(f"{prefix}eliminar") == 'on':
            db.session.delete(hijo)
        else:
            nuevo_nombre = to_upper(request.form.get(f"{prefix}nombre"))
            nueva_fecha = parse_date(request.form.get(f"{prefix}fecha"))
            if nuevo_nombre:
                hijo.nombre = nuevo_nombre
                hijo.fecha_nacimiento = nueva_fecha

    nombre_nuevo_hijo = to_upper(request.form.get('nombre_hijo_nuevo'))
    fecha_nuevo_hijo = parse_date(request.form.get('fecha_hijo_nuevo'))
    if nombre_nuevo_hijo:
        db.session.add(Hijo(socio_id=socio.id, nombre=nombre_nuevo_hijo, fecha_nacimiento=fecha_nuevo_hijo))

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
        db.session.add(HistorialCargo(socio_id=socio.id, cargo=to_upper(nuevo_cargo), periodo=to_upper(periodo_nuevo), es_actual=es_actual))
        
    db.session.commit()
    flash('Información actualizada correctamente', 'success')
    return redirect(url_for('gestion_socios'))

@app.route('/cumpleanos-mes')
def cumpleanos_mes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    mes_actual = datetime.now().month
    todos_socios = Socio.query.order_by(Socio.nombre_completo.asc()).all()
    festividades = []
    for socio in todos_socios:
        if socio.fecha_nacimiento and socio.fecha_nacimiento.month == mes_actual:
            festividades.append({'dia': socio.fecha_nacimiento.day, 'fecha_str': socio.fecha_nacimiento.strftime('%d/%m/%Y'), 'tipo': 'CUMPLEAÑOS SOCIO', 'persona': socio.nombre_completo, 'detalle': f"SOCIO ID: {socio.numero_socio or socio.id}"})
        if socio.fecha_nacimiento_esposa and socio.fecha_nacimiento_esposa.month == mes_actual:
            festividades.append({'dia': socio.fecha_nacimiento_esposa.day, 'fecha_str': socio.fecha_nacimiento_esposa.strftime('%d/%m/%Y'), 'tipo': 'CUMPLEAÑOS CÓNYUGE', 'persona': socio.nombre_esposa or 'CÓNYUGE', 'detalle': f"CÓNYUGE DE: {socio.nombre_completo}"})
        if socio.aniversario_matrimonio and socio.aniversario_matrimonio.month == mes_actual:
            festividades.append({'dia': socio.aniversario_matrimonio.day, 'fecha_str': socio.aniversario_matrimonio.strftime('%d/%m/%Y'), 'tipo': 'ANIVERSARIO DE BODAS', 'persona': f"{socio.nombre_completo} Y {socio.nombre_esposa or 'CÓNYUGE'}", 'detalle': "ANIVERSARIO MATRIMONIAL"})
        if socio.hijos:
            for hijo in socio.hijos:
                if hijo.fecha_nacimiento and hijo.fecha_nacimiento.month == mes_actual:
                    festividades.append({'dia': hijo.fecha_nacimiento.day, 'fecha_str': hijo.fecha_nacimiento.strftime('%d/%m/%Y'), 'tipo': 'CUMPLEAÑOS HIJO(A)', 'persona': hijo.nombre, 'detalle': f"HIJO(A) DE: {socio.nombre_completo}"})
    festividades = sorted(festividades, key=lambda x: x['dia'])
    meses_es = {1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL", 5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO", 9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"}
    return render_template('cumpleanos.html', festividades=festividades, mes_actual=meses_es.get(mes_actual, ""))

@app.route('/autoridades')
def gestion_autoridades():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('autoridades.html', autoridades=AutoridadRotaria.query.all())

@app.route('/autoridades/guardar', methods=['POST'])
def guardar_autoridad():
    if 'user_id' not in session or session.get('rol') not in ['ADMIN', 'TESORERO', 'PRESIDENTE']:
        flash('No autorizado', 'danger')
        return redirect(url_for('gestion_autoridades'))
    auth_id = request.form.get('auth_id')
    nombre = to_upper(request.form.get('nombre'))
    cargo = to_upper(request.form.get('cargo'))
    nivel = to_upper(request.form.get('nivel'))
    correo = request.form.get('correo')
    telefono = to_upper(request.form.get('telefono'))
    if auth_id:
        autoridad = AutoridadRotaria.query.get_or_404(auth_id)
        autoridad.nombre, autoridad.cargo, autoridad.nivel, autoridad.correo, autoridad.telefono = nombre, cargo, nivel, correo, telefono
    else:
        db.session.add(AutoridadRotaria(nombre=nombre, cargo=cargo, nivel=nivel, correo=correo, telefono=telefono))
    db.session.commit()
    flash('Autoridad guardada correctamente', 'success')
    return redirect(url_for('gestion_autoridades'))

@app.route('/autoridades/eliminar/<int:id>')
def eliminar_autoridad(id):
    if 'user_id' not in session or session.get('rol') not in ['ADMIN', 'TESORERO', 'PRESIDENTE']:
        flash('No autorizado', 'danger')
        return redirect(url_for('gestion_autoridades'))
    db.session.delete(AutoridadRotaria.query.get_or_404(id))
    db.session.commit()
    flash('Autoridad eliminada', 'success')
    return redirect(url_for('gestion_autoridades'))

# --- MÓDULO DE TESORERÍA ---
@app.route('/tesoreria')
def modulo_tesoreria():
    if 'user_id' not in session or session.get('rol') not in ['ADMIN', 'TESORERO', 'PRESIDENTE']:
        flash('Acceso restringido al módulo de Tesorería.', 'danger')
        return redirect(url_for('menu_principal'))
    return render_template('tesoreria_menu.html')

@app.route('/tesoreria/cuotas-sociales')
def cuotas_sociales():
    if 'user_id' not in session or session.get('rol') not in ['ADMIN', 'TESORERO', 'PRESIDENTE']:
        flash('Acceso restringido.', 'danger')
        return redirect(url_for('menu_principal'))
    
    db.session.expire_all()
    socios = Socio.query.order_by(Socio.nombre_completo.asc()).all()
    
    meses_control = [
        "JUL 2025", "AGO 2025", "SEP 2025", "OCT 2025", "NOV 2025", "DIC 2025",
        "ENE 2026", "FEB 2026", "MAR 2026", "ABR 2026", "MAY 2026", "JUN 2026",
        "JUL 2026", "AGO 2026", "SEP 2026", "OCT 2026", "NOV 2026", "DIC 2026",
        "ENE 2027", "FEB 2027", "MAR 2027", "ABR 2027", "MAY 2027", "JUN 2027"
    ]
    
    config_teso = ConfiguracionTesoreria.query.first()
    saldo_inicial = config_teso.saldo_inicial if config_teso else 0.0
    
    meses_validos_reporte = [
        "FEB 2026", "MAR 2026", "ABR 2026", "MAY 2026", "JUN 2026",
        "JUL 2026", "AGO 2026", "SEP 2026", "OCT 2026", "NOV 2026", "DIC 2026",
        "ENE 2027", "FEB 2027", "MAR 2027", "ABR 2027", "MAY 2027", "JUN 2027"
    ]
    
    total_recaudado_valido = PagoCuota.query.filter(PagoCuota.mes_anio.in_(meses_validos_reporte)).with_entities(db.func.sum(PagoCuota.monto)).scalar() or 0.0
    saldo_total_general = saldo_inicial + total_recaudado_valido
    
    ultimo_pago = PagoCuota.query.get(request.args.get('recibo_id')) if request.args.get('recibo_id') else None
    
    return render_template('tesoreria.html', socios=socios, meses=meses_control, ultimo_pago=ultimo_pago, saldo_inicial=saldo_inicial, saldo_total_general=saldo_total_general)

@app.route('/tesoreria/actualizar-saldo-inicial', methods=['POST'])
def actualizar_saldo_inicial():
    if 'user_id' not in session or session.get('rol') not in ['ADMIN', 'TESORERO', 'PRESIDENTE']:
        flash('No autorizado.', 'danger')
        return redirect(url_for('menu_principal'))
    
    password = request.form.get('password')
    nuevo_saldo = float(request.form.get('saldo_inicial', 0.0))
    
    user = Usuario.query.get(session['user_id'])
    if user and check_password_hash(user.password_hash, password):
        config = ConfiguracionTesoreria.query.first()
        if not config:
            config = ConfiguracionTesoreria(saldo_inicial=nuevo_saldo)
            db.session.add(config)
        else:
            config.saldo_inicial = nuevo_saldo
        db.session.commit()
        flash('¡Saldo inicial actualizado exitosamente con autorización!', 'success')
    else:
        flash('Contraseña incorrecta. No se pudo actualizar el saldo inicial.', 'danger')
        
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
    
    ultimo_pago_creado = None
    if socio_id and meses_pagados:
        for m in meses_pagados:
            mes_limpio = m.strip().upper()
            existente = PagoCuota.query.filter_by(socio_id=socio_id, mes_anio=mes_limpio).first()
            if not existente:
                pago = PagoCuota(socio_id=socio_id, mes_anio=mes_limpio, monto=500.0, metodo_pago=metodo, referencia=referencia)
                db.session.add(pago)
                db.session.flush()
                ultimo_pago_creado = pago
        db.session.commit()
        flash('Pago(s) registrado(s) correctamente.', 'success')
        if ultimo_pago_creado:
            return redirect(url_for('cuotas_sociales', recibo_id=ultimo_pago_creado.id))
    else:
        flash('Debe seleccionar al menos un mes y un socio.', 'warning')
        
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
        pago.monto = float(request.form.get('monto', 500.0))
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
    meses_es = {"January": "ENERO", "February": "FEBRERO", "March": "MARZO", "April": "ABRIL", "May": "MAYO", "June": "JUNIO", "July": "JULIO", "August": "AGOSTO", "September": "SEPTIEMBRE", "October": "OCTUBRE", "November": "NOVIEMBRE", "December": "DICIEMBRE"}
    dias_es = {"Monday": "LUNES", "Tuesday": "MARTES", "Wednesday": "MIÉRCOLES", "Thursday": "JUEVES", "Friday": "VIERNES", "Saturday": "SÁBADO", "Sunday": "DOMINGO"}
    ahora = datetime.now()
    fecha_recibo = f"{dias_es.get(ahora.strftime('%A'), '')}, {ahora.day} DE {meses_es.get(ahora.strftime('%B'), '')} DE {ahora.year}"
    return render_template('recibo_pdf.html', pago=pago, fecha_recibo=fecha_recibo)

@app.route('/tesoreria/estado-cuenta-pdf/<int:socio_id>')
def estado_cuenta_pdf(socio_id):
    if 'user_id' not in session or session.get('rol') not in ['ADMIN', 'TESORERO', 'PRESIDENTE']:
        return redirect(url_for('login'))
    
    socio = Socio.query.get_or_404(socio_id)
    meses_control = [
        "JUL 2025", "AGO 2025", "SEP 2025", "OCT 2025", "NOV 2025", "DIC 2025",
        "ENE 2026", "FEB 2026", "MAR 2026", "ABR 2026", "MAY 2026", "JUN 2026",
        "JUL 2026", "AGO 2026", "SEP 2026", "OCT 2026", "NOV 2026", "DIC 2026",
        "ENE 2027", "FEB 2027", "MAR 2027", "ABR 2027", "MAY 2027", "JUN 2027"
    ]
    
    meses_es = {"January": "ENERO", "February": "FEBRERO", "March": "MARZO", "April": "ABRIL", "May": "MAYO", "June": "JUNIO", "July": "JULIO", "August": "AGOSTO", "September": "SEPTIEMBRE", "October": "OCTUBRE", "November": "NOVIEMBRE", "December": "DICIEMBRE"}
    dias_es = {"Monday": "LUNES", "Tuesday": "MARTES", "Wednesday": "MIÉRCOLES", "Thursday": "JUEVES", "Friday": "VIERNES", "Saturday": "SÁBADO", "Sunday": "DOMINGO"}
    
    ahora = datetime.now()
    fecha_actual_str = f"{dias_es.get(ahora.strftime('%A'), '')}, {ahora.day} DE {meses_es.get(ahora.strftime('%B'), '')} DE {ahora.year}"
    
    return render_template('estado_cuenta_pdf.html', socio=socio, meses=meses_control, fecha_actual_str=fecha_actual_str)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index_publico'))

if __name__ == '__main__':
    app.run(debug=True)
