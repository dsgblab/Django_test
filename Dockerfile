FROM python:3.10-slim

# Environment config
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install build dependencies and system packages
RUN apt-get update && apt-get install -y \
    curl gnupg2 apt-transport-https \
    build-essential gcc g++ \
    locales \
    && rm -rf /var/lib/apt/lists/*

# Set up locale
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

# Install Microsoft SQL Server ODBC Driver - trying Ubuntu repo as fallback
RUN curl -sSL https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl -sSL https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && echo "Available mssql packages:" \
    && apt-cache search mssql \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && ACCEPT_EULA=Y apt-get install -y mssql-tools \
    && echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bashrc \
    && apt-get install -y unixodbc-dev \
    && apt-get install -y libgssapi-krb5-2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

# Create static directory and collect static files
RUN mkdir -p /app/static
RUN python manage.py collectstatic --noinput
# Copy project files
COPY . .

# Expose port
EXPOSE 8001

CMD ["gunicorn", "myproject.wsgi:application", "--bind", "0.0.0.0:8001"]
