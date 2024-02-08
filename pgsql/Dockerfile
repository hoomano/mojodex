# Use the Postgres image from Andrew Kane with pgvector as the base image
# https://hub.docker.com/r/ankane/pgvector
FROM ankane/pgvector:latest

# Create the structure of the database
COPY create-mojodex-db.sql /docker-entrypoint-initdb.d/01_create-mojodex-db.sql

# Copy the data into the database
COPY init-mojodex-data.sql /docker-entrypoint-initdb.d/02_init-mojodex-data.sql

# Expose the PostgreSQL port
EXPOSE 5432
