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
    
    # Manejar la subida de la foto local
    file = request.files.get('foto_archivo')
    if file and file.filename != '':
        if allowed_file(file.filename):
            filename = secure_filename(f"socio_{socio.id}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            socio.foto_url = f"/{filepath}" if not filepath.startswith('/') else filepath
    
    # Agregar nuevo cargo (histórico o actual)
    nuevo_cargo = request.form.get('cargo_nuevo')
    periodo_nuevo = request.form.get('periodo_nuevo')
    es_actual = request.form.get('es_actual') == 'on'
    
    if nuevo_cargo and periodo_nuevo:
        # Si se marca como actual, desactivamos los actuales previos
        if es_actual:
            for c in socio.cargos:
                c.es_actual = False
                
        cargo_db = HistorialCargo(
            socio_id=socio.id, 
            cargo=nuevo_cargo, 
            periodo=periodo_nuevo, 
            es_actual=es_actual
        )
        db.session.add(cargo_db)
        
    db.session.commit()
    flash('Información del socio y cargos actualizados correctamente', 'success')
    return redirect(url_for('gestion_socios'))
