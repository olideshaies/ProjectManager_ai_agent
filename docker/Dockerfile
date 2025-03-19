FROM timescale/timescaledb-ha:pg16

# Install pgvector
RUN apt-get update \
    && apt-get install -y postgresql-common \
    && yes | /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh \
    && apt-get install -y postgresql-16-pgvector

# Copy initialization script
COPY ./init.sql /docker-entrypoint-initdb.d/
