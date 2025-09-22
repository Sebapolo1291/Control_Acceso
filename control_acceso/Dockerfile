# Usa una imagen base oficial de Python
FROM python:3.13-rc-slim-bullseye

# Establece el directorio de trabajo en el contenedor
WORKDIR /usr/src/app

# Instala las dependencias del sistema
RUN apt-get update && apt-get install -y \
    libaio1 \
    && rm -rf /var/lib/apt/lists/*

# Copia el archivo de requerimientos y lo instala
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código de la aplicación al directorio de trabajo
COPY . .

# Establece las variables de entorno necesarias para Django
ENV DJANGO_SETTINGS_MODULE=control_acceso.settings
ENV PYTHONUNBUFFERED=1

# Expone el puerto en el que la aplicación se ejecutará
EXPOSE 8000

# Ejecuta las migraciones y el servidor de desarrollo de Django
CMD ["sh", "-c", "python manage.py runserver 0.0.0.0:8000"]