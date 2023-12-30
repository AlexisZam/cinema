# syntax=docker/dockerfile:1.7.0

FROM postgres:16.3-bookworm

USER postgres

ENV PGDATA= PGDATA=/var/lib/postgresql/data/pgdata
    # POSTGRES_PASSWORD_FILE=/run/secrets/postgres-password

HEALTHCHECK --interval=3s --timeout=3s CMD ["pg_isready"]

# CMD ["postgres", "--log-destination=jsonlog,stderr", "--logging-collector=1"]
