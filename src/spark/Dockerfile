FROM bitnami/spark:3.5

USER root

# Install Python dependencies
COPY src/spark/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Download PostgreSQL JDBC driver
RUN curl -fSL https://jdbc.postgresql.org/download/postgresql-42.7.1.jar \
    -o /opt/bitnami/spark/jars/postgresql-42.7.1.jar

USER 1001

WORKDIR /app

# Copy config module so imports resolve
COPY config/ /app/config/

# Copy source code
COPY src/ /app/src/

ENV PYTHONPATH=/app
