# syntax=docker/dockerfile:1.7.0

FROM node:21.7.2-slim

RUN corepack enable

USER node

WORKDIR /home/node/frontend/

COPY --chown=node:node ./frontend/ ./

RUN --mount=type=cache,target=/root/.local/share/pnpm/store/ \
    pnpm install --frozen-lockfile

CMD ["pnpm", "exec", "webpack", "serve", "--mode=development"]

EXPOSE 8080
