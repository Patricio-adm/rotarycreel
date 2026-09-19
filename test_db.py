echo "import psycopg2

try:
    print('Probando conexión con la nueva contraseña...')
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres.smbrfdwruccudlcjdabs',
        password='rotary4110creel',
        host='aws-0-ca-central-1.pooler.supabase.com',
        port=6543,
        connect_timeout=5
    )
    print('¡CONEXIÓN EXITOSA!')
    conn.close()
except Exception as e:
    print('\n--- ERROR DETECTADO ---')
    print(e)" > test_db.py
