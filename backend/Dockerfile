ARG ORM

FROM $ORM

WORKDIR /home/python/backend/

COPY --chown=python:python ./backend/ ./

RUN --mount=type=cache,id=backend,target=./.cache/pypoetry/,uid=102,gid=102 \
    "${POETRY_HOME?}/bin/poetry" install \
 && rm -r "${POETRY_HOME?}"

CMD ["uvicorn", "src.api:app", "--host=0.0.0.0", "--reload"]

EXPOSE 8000
