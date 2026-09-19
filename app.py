from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'clave_secreta_rotary_creel' # Cambiala por una clave segura

# Configuración de la base de datos (mantiene tu conexión a Supabase)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://postgres.smbrfdwruccudlcjdabs:rotary4110creel@aws-0-ca-central-1.pooler.supabase.com:6543/postgres')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app, engine_options={
    "pool_pre_ping": True,
    "pool_recycle": 300,
})

# Modelo de Usuario para el Login
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

# Crear las tablas en la base de datos si no existen
with app.app_context():
    db.create_all()
    # Crear un usuario administrador por defecto si no hay ninguno (admin / rotary2026)
    if not Usuario.query.filter_by(username='admin').first():
        admin_user = Usuario(
            username='admin',
            password_hash=generate_password_hash('rotary2026')
        )
        db.session.add(admin_user)
        db.session.commit()

# Ruta de Login (Página Principal)
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

# Menú Principal (después de iniciar sesión)
@app.route('/menu')
def menu_principal():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('menu.html')

# Cerrar sesión
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
