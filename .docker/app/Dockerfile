# syntax=docker/dockerfile:1
FROM node:22.22-bullseye-slim AS base
SHELL ["/bin/bash", "--login", "-c"]

WORKDIR /app

EXPOSE 8081

RUN apt update && apt install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

COPY webapp/package.json webapp/yarn.lock ./

# Using a custom node_modules location to avoid mounting it outside of docker
RUN --mount=type=cache,target=/root/.cache/yarn yarn install --frozen-lockfile --modules-folder /node_modules

# dev target: deps installed, source mounted at runtime — no production build.
# Also installs the system libraries the Cypress test runner needs (GTK/X11
# runtime libs plus xvfb for a virtual display), so the webapp test suites can
# run inside the container.
FROM base AS dev
RUN apt update \
    && apt install -y --no-install-recommends \
        libgtk2.0-0 \
        libgtk-3-0 \
        libgbm-dev \
        libnotify-dev \
        libnss3 \
        libxss1 \
        libasound2 \
        libxtst6 \
        xauth \
        xvfb \
    && rm -rf /var/lib/apt/lists/*
COPY webapp ./

# build target: runs the production webpack bundle. Derives from `base` rather
# than `dev` so production builds don't pull in the Cypress system libraries.
FROM base AS build
COPY webapp ./
# These get replaced by the entrypoint script for production builds.
# Set the real values in `.env` files or an external docker-compose.
ENV NODE_ENV=production
ARG VUE_APP_API_URL=magic-api-url
ARG VUE_APP_LOGO_URL=magic-logo-url
ARG VUE_APP_HOMEPAGE_URL=magic-homepage-url
ARG VUE_APP_EDITABLE_INVENTORY=magic-setting
ARG VUE_APP_WEBSITE_TITLE=magic-title
ARG VUE_APP_QR_CODE_RESOLVER_URL=magic-qr-code-resolver-url
ARG VUE_APP_AUTOMATICALLY_GENERATE_ID_DEFAULT=magic-generate-id-setting
# Version source for scripts/get-version.js. Provided as a build arg so the
# build layer doesn't depend on `.git` (which would invalidate cache every commit).
ARG VUE_APP_GIT_VERSION=0.0.0+ci
ENV VUE_APP_GIT_VERSION=${VUE_APP_GIT_VERSION}

RUN /node_modules/.bin/vue-cli-service build

FROM node:22.22-bullseye-slim AS production

ENV PATH=$PATH:/node_modules/.bin
COPY ./.docker/app_entrypoint.sh /app/

COPY webapp/package.json webapp/yarn.lock ./

COPY --from=build /app/dist /app/dist
RUN --mount=type=cache,target=/root/.cache/yarn yarn install --frozen-lockfile --modules-folder /node_modules --production

CMD [ "/bin/bash", "-c", "/app/app_entrypoint.sh" ]

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD node -e "fetch('http://localhost:8081').then(r => process.exit(r.ok ? 0 : 1)).catch(() => process.exit(1))"
