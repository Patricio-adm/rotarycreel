import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres.smbrfdwruccudlcjdabs:rotary4110creel@aws-0-ca-central-1.pooler.supabase.com:6543/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'clave_secreta_para_flask_123'

# Añadimos pool_pre_ping para evitar que la conexión con Supabase se caiga inesperadamente
db = SQLAlchemy(app, engine_options={
    "pool_pre_ping": True,
    "pool_recycle": 300,
})

class Hijo(db.Model):
    __tablename__ = 'hijos'
    id = db.Column(db.Integer, primary_key=True)
    socio_id = db.Column(db.Integer, db.ForeignKey('socios.id', ondelete='CASCADE'), nullable=False)
    nombre = db.Column(db.String(150), nullable=False)
    fecha_nacimiento = db.Column(db.Date)

class Socio(db.Model):
    __tablename__ = 'socios'
    id = db.Column(db.Integer, primary_key=True)
    numero_socio = db.Column(db.String(50), unique=True)
    tipo_socio = db.Column(db.String(20), default='ACTIVO')
    nombre_completo = db.Column(db.String(150), nullable=False)
    telefono = db.Column(db.String(30))
    correo = db.Column(db.String(100))
    fecha_nacimiento = db.Column(db.Date)
    
    # Domicilio
    calle_numero = db.Column(db.String(200))
    colonia = db.Column(db.String(100))
    codigo_postal = db.Column(db.String(10))
    ciudad = db.Column(db.String(100))
    estado = db.Column(db.String(100))
    
    # Datos familiares / Matrimonio
    estado_civil = db.Column(db.String(20))
    nombre_esposa = db.Column(db.String(150))
    fecha_nacimiento_esposa = db.Column(db.Date)
    aniversario_matrimonio = db.Column(db.Date)
    telefono_esposa = db.Column(db.String(30))
    
    # Emergencia
    telefono_emergencia = db.Column(db.String(30))
    
    hijos = db.relationship('Hijo', backref='socio', cascade='all, delete-orphan', lazy=True)
    es_activo = db.Column(db.Boolean, default=True)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    try:
        socios = Socio.query.filter_by(es_activo=True).all()
    except Exception as e:
        socios = []
        print(f"Error al conectar con la base de datos: {e}")
    return render_template('socios.html', socios=socios)

@app.route('/socio/nuevo', methods=['GET', 'POST'])
def agregar_socio():
    if request.method == 'POST':
        nombre = request.form.get('nombre_completo', '').strip().upper()
        num_socio = request.form.get('numero_socio', '').strip().upper()
        tipo_socio = request.form.get('tipo_socio', 'ACTIVO')
        telefono = request.form.get('telefono', '').strip().upper()
        correo = request.form.get('correo', '').strip()
        
        fnac_str = request.form.get('fecha_nacimiento')
        fecha_nacimiento = datetime.strptime(fnac_str, '%Y-%m-%d').date() if fnac_str else None
        
        calle_numero = request.form.get('calle_numero', '').strip().upper()
        colonia = request.form.get('colonia', '').strip().upper()
        codigo_postal = request.form.get('codigo_postal', '').strip()
        ciudad = request.form.get('ciudad', '').strip().upper()
        estado = request.form.get('estado', '').strip().upper()
        
        estado_civil = request.form.get('estado_civil', '').strip().upper()
        nombre_esposa = request.form.get('nombre_esposa', '').strip().upper() if estado_civil == 'CASADO' else None
        
        fnac_esp_str = request.form.get('fecha_nacimiento_esposa')
        fecha_nacimiento_esposa = datetime.strptime(fnac_esp_str, '%Y-%m-%d').date() if fnac_esp_str and estado_civil == 'CASADO' else None
        
        aniv_str = request.form.get('aniversario_matrimonio')
        aniversario_matrimonio = datetime.strptime(aniv_str, '%Y-%m-%d').date() if aniv_str and estado_civil == 'CASADO' else None
        
        telefono_esposa = request.form.get('telefono_esposa', '').strip().upper() if estado_civil == 'CASADO' else None
        telefono_emergencia = request.form.get('telefono_emergencia', '').strip().upper()
        
        nuevo_socio = Socio(
            numero_socio=num_socio if num_socio else None,
            tipo_socio=tipo_socio,
            nombre_completo=nombre,
            telefono=telefono if telefono else None,
            correo=correo if correo else None,
            fecha_nacimiento=fecha_nacimiento,
            calle_numero=calle_numero if calle_numero else None,
            colonia=colonia if colonia else None,
            codigo_postal=codigo_postal if codigo_postal else None,
            ciudad=ciudad if ciudad else None,
            estado=estado if estado else None,
            estado_civil=estado_civil if estado_civil else None,
            nombre_esposa=nombre_esposa,
            fecha_nacimiento_esposa=fecha_nacimiento_esposa,
            aniversario_matrimonio=aniversario_matrimonio,
            telefono_esposa=telefono_esposa if telefono_esposa else None,
            telefono_emergencia=telefono_emergencia if telefono_emergencia else None
        )
        
        db.session.add(nuevo_socio)
        db.session.flush()
        
        nombres_hijos = request.form.getlist('hijo_nombre[]')
        fechas_hijos = request.form.getlist('hijo_fnac[]')
        
        for i in range(len(nombres_hijos)):
            h_nombre = nombres_hijos[i].strip().upper()
            if h_nombre:
                h_fnac = None
                if i < len(fechas_hijos) and fechas_hijos[i]:
                    try:
                        h_fnac = datetime.strptime(fechas_hijos[i], '%Y-%m-%d').date()
                    except:
                        pass
                nuevo_hijo = Hijo(socio_id=nuevo_socio.id, nombre=h_nombre, fecha_nacimiento=h_fnac)
                db.session.add(nuevo_hijo)
                
        db.session.commit()
        return redirect(url_for('index'))
        
    return render_template('nuevo_socio.html')

@app.route('/socio/editar/<int:id>', methods=['GET', 'POST'])
def editar_socio(id):
    socio = Socio.query.get_or_404(id)
    if request.method == 'POST':
        socio.nombre_completo = request.form.get('nombre_completo', '').strip().upper()
        socio.numero_socio = request.form.get('numero_socio', '').strip().upper() or None
        socio.tipo_socio = request.form.get('tipo_socio', 'ACTIVO')
        socio.telefono = request.form.get('telefono', '').strip().upper() or None
        socio.correo = request.form.get('correo', '').strip() or None
        
        fnac_str = request.form.get('fecha_nacimiento')
        socio.fecha_nacimiento = datetime.strptime(fnac_str, '%Y-%m-%d').date() if fnac_str else None
        
        socio.calle_numero = request.form.get('calle_numero', '').strip().upper() or None
        socio.colonia = request.form.get('colonia', '').strip().upper() or None
        socio.codigo_postal = request.form.get('codigo_postal', '').strip() or None
        socio.ciudad = request.form.get('ciudad', '').strip().upper() or None
        socio.estado = request.form.get('estado', '').strip().upper() or None
        
        socio.estado_civil = request.form.get('estado_civil', '').strip().upper() or None
        if socio.estado_civil == 'CASADO':
            socio.nombre_esposa = request.form.get('nombre_esposa', '').strip().upper() or None
            fnac_esp_str = request.form.get('fecha_nacimiento_esposa')
            socio.fecha_nacimiento_esposa = datetime.strptime(fnac_esp_str, '%Y-%m-%d').date() if fnac_esp_str else None
            aniv_str = request.form.get('aniversario_matrimonio')
            socio.aniversario_matrimonio = datetime.strptime(aniv_str, '%Y-%m-%d').date() if aniv_str else None
            socio.telefono_esposa = request.form.get('telefono_esposa', '').strip().upper() or None
        else:
            socio.nombre_esposa = None
            socio.fecha_nacimiento_esposa = None
            socio.aniversario_matrimonio = None
            socio.telefono_esposa = None
            
        socio.telefono_emergencia = request.form.get('telefono_emergencia', '').strip().upper() or None
        
        Hijo.query.filter_by(socio_id=socio.id).delete()
        nombres_hijos = request.form.getlist('hijo_nombre[]')
        fechas_hijos = request.form.getlist('hijo_fnac[]')
        
        for i in range(len(nombres_hijos)):
            h_nombre = nombres_hijos[i].strip().upper()
            if h_nombre:
                h_fnac = None
                if i < len(fechas_hijos) and fechas_hijos[i]:
                    try:
                        h_fnac = datetime.strptime(fechas_hijos[i], '%Y-%m-%d').date()
                    except:
                        pass
                nuevo_hijo = Hijo(socio_id=socio.id, nombre=h_nombre, fecha_nacimiento=h_fnac)
                db.session.add(nuevo_hijo)
                
        db.session.commit()
        return redirect(url_for('index'))
        
    return render_template('editar_socio.html', socio=socio)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
