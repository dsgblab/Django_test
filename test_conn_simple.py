import pyodbc

conn_str = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=EQ065;'
    'DATABASE=django_test_db;'
    'Trusted_Connection=yes;'
    'TrustServerCertificate=yes;'
)

try:
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        if result:
            print("Conexión exitosa con Windows Authentication, prueba OK:", result[0])
        else:
            print("Conexión OK, pero no devolvió resultados")
except Exception as e:
    print("Error al conectar:", e)
