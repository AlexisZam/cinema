ARG ORM

FROM $ORM

WORKDIR /home/python/loaders/

COPY --chown=python:python ./loaders/ ./

RUN --mount=type=cache,id=loaders,target=./.cache/pypoetry/,uid=102,gid=102 \
    "${POETRY_HOME?}/bin/poetry" install \
 && rm -r "${POETRY_HOME?}"

CMD ["python", "-m", "loaders.create"]
