import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
import os
os.environ['PATH'] = r'C:\instantclient_23_7' + ";" + os.environ['PATH']

# Configuración de conexión a MySQL
mysql_engine = create_engine('mysql+mysqlconnector://root:@localhost/control_acceso')  # Cambiar por tus datos

# Configuración de conexión a Oracle
oracle_engine = create_engine('oracle+cx_oracle://CONTROL_ACCESO:S3b4st14n_T3sT@test-oracle-db.minseg.gob.ar:1521/testoracledb')

# Leer datos desde MySQL
df = pd.read_sql('SELECT * FROM visits', mysql_engine)

# Procesamiento: convertir hora_entrada/salida a timestamp (asumiendo formato 'HH:MM:SS')
def text_to_timestamp(fecha, hora_texto):
    try:
        return datetime.strptime(f"{fecha} {hora_texto.strip()}", "%Y-%m-%d %H:%M:%S")
    except:
        return None

df['HORA_ENTRADA'] = df.apply(lambda row: text_to_timestamp(row['fecha'], row['hora_entrada']), axis=1)
df['HORA_SALIDA'] = df.apply(lambda row: text_to_timestamp(row['fecha'], row['hora_salida']) if row['hora_salida'] else None, axis=1)

# Renombrar columnas para Oracle
df_oracle = df.rename(columns={
    'id': 'ID',
    'fecha': 'FECHA',
    'HORA_ENTRADA': 'HORA_ENTRADA',
    'HORA_SALIDA': 'HORA_SALIDA',
    'nombre': 'RECEPTOR_NOMBRE',
    'apellido': 'RECEPTOR_APELLIDO',
    'observaciones': 'OBSERVACIONES',
    'created_at': 'CREATED_AT',
    'updated_at': 'UPDATED_AT',
    'area_id': 'AREA_ID',
    'user_id': 'CREATED_BY_ID',
    'person_id': 'PERSON_ID',
    'sede_id': 'SEDE_ID',
    'subarea_id': 'SUBAREA_ID'
})

# Elegir solo columnas compatibles con Oracle
columnas_oracle = [
     'FECHA', 'HORA_ENTRADA', 'HORA_SALIDA', 'RECEPTOR_NOMBRE', 'RECEPTOR_APELLIDO',
    'OBSERVACIONES', 'CREATED_AT', 'UPDATED_AT', 'AREA_ID', 'CREATED_BY_ID',
    'PERSON_ID', 'SEDE_ID', 'SUBAREA_ID'
]
df_oracle = df_oracle[columnas_oracle]

# Insertar datos en Oracle
df_oracle.to_sql('CONTROL_ACCESO_VISIT', oracle_engine, schema='CONTROL_ACCESO', if_exists='append', index=False, chunksize=500)

print("Migración completada con éxito.")
