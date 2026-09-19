# Menú Principal (ya con inicio de sesión requerido)
@app.route('/menu')
def menu_principal():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('menu.html')

# Ruta de Gestión de Socios (Reemplaza 'socios' por el nombre de tu función actual si es distinto)
@app.route('/socios')
def gestion_socios():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # Aquí puedes llamar a tu lógica o plantilla existente de socios
    # Ejemplo: return render_template('socios.html', socios=Socios.query.all())
    return render_template('socios.html') 

# Ruta de Tesorería (Reemplaza 'tesoreria' por el nombre de tu función actual si es distinto)
@app.route('/tesoreria')
def modulo_tesoreria():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # Aquí puedes llamar a tu lógica o plantilla existente de tesorería
    return render_template('tesoreria.html')
