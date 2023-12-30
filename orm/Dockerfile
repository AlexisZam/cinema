FROM python:3.13.1-bookworm

RUN adduser --group --system --home /home/python/ --uid 102 python

WORKDIR /home/python

USER python

ENV POETRY_HOME=/home/python/poetry \
    POETRY_VIRTUALENVS_CREATE=0 \
    VIRTUAL_ENV=/home/python/.venv
ENV PATH=${VIRTUAL_ENV?}/bin/:$PATH

RUN python -m venv ${POETRY_HOME?} \
 && ${POETRY_HOME?}/bin/pip install poetry==1.8.3 \
 && python -m venv --without-pip .venv

COPY --chown=python:python ./orm/ ./orm/
