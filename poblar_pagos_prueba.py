from app import app, db, Socio, PagoCuota
from datetime import date

def poblar_pagos():
    with app.app_context():
        # Buscamos tu usuario en la base de datos
        socio = Socio.query.filter(Socio.nombre_completo.ilike('%PATRICIO%')).first()
        
        if not socio:
            print("No se encontró al socio Patricio en la base de datos.")
            return
        
        print(f"Socio encontrado: {socio.nombre_completo} (ID: {socio.id})")
        
        # Meses de prueba a registrar
        meses_prueba = ["JUN 2025", "JUL 2025", "AGO 2025", "SEP 2025"]
        
        for mes in meses_prueba:
            # Verificamos si ya existe
            existente = PagoCuota.query.filter_by(socio_id=socio.id, mes_anio=mes).first()
            if not existente:
                nuevo_pago = PagoCuota(
                    socio_id=socio.id,
                    mes_anio=mes,
                    monto=500.0,
                    metodo_pago="TRANSFERENCIA",
                    fecha_pago=date.today(),
                    referencia="PRUEBA001"
                )
                db.session.add(nuevo_pago)
                print(f"   -> Registrando pago para el mes: {mes}")
            else:
                print(f"   -> El mes {mes} ya tenía un pago registrado.")
                
        db.session.commit()
        print("\n¡Pagos de prueba insertados con éxito! Ya puedes revisar tu matriz en la web.")

if __name__ == '__main__':
    poblar_pagos()
