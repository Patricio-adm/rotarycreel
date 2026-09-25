from app import app, db, Socio, PagoCuota

def verificar_saldos_socios():
    with app.app_context():
        socios = Socio.query.order_by(Socio.nombre_completo.asc()).all()
        
        print("=" * 75)
        print(f"{'DIAGNÓSTICO DE PAGOS REGISTRADOS EN LA BASE DE DATOS':^75}")
        print("=" * 75)
        
        total_pagos_bd = PagoCuota.query.count()
        print(f"Total de registros de pagos encontrados en la tabla: {total_pagos_bd}\n")
        
        for socio in socios:
            print(f"Socio: {socio.nombre_completo}")
            if socio.pagos:
                meses_registrados = [p.mes_anio for p in socio.pagos]
                print(f"   -> Pagos en BD: {meses_registrados}")
            else:
                print(f"   -> Sin pagos registrados en la base de datos.")
            print("-" * 75)

if __name__ == '__main__':
    verificar_saldos_socios()
