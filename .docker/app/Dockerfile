# syntax=docker/dockerfile:1
# Both frontend targets collect panels from the corresponding plugin-enabled
# API image supplied by Docker Compose as a named build context.
FROM plugin_environment AS plugin-panels
COPY --exclude=public/custom webapp /webapp
RUN /opt/.venv/bin/invoke dev.collect-plugin-panels

# Copy plugin's package.json files alone (yarn workspaces), so that editing a plugin's
# components does not invalidate the dependency install below
RUN mkdir /plugin-packages \
    && cd /webapp/src/plugins \
    && find . -mindepth 2 -maxdepth 2 -name package.json -exec cp --parents {} /plugin-packages/ \;

# Single source for the Node image used by all Node-based targets
FROM node:22.23.4-trixie-slim AS node_base
# Refresh the system CA store on top of the base image, for all Node-based targets
RUN apt update && apt install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*

# deps target: core webapp dependencies only. Does not depend on the API image,
# so it can build in parallel with it and stays cached across plugin changes.
FROM node_base AS deps
SHELL ["/bin/bash", "--login", "-c"]

WORKDIR /app

EXPOSE 8081

RUN apt update && apt install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

COPY webapp/package.json webapp/yarn.lock ./

# Using a custom node_modules location to avoid mounting it outside of docker.
RUN --mount=type=cache,target=/root/.cache/yarn \
    yarn install --frozen-lockfile --modules-folder /node_modules

FROM deps AS base
COPY --from=plugin-panels /plugin-packages ./src/plugins

# Plugin dependencies are not in the committed yarn.lock, so when plugins declare
# any, install them on top of the core deps with --pure-lockfile (core pins are
# kept; the lockfile is not written). Plugin-specific versions that conflict with
# the webapp's are nested in src/plugins/<package>/node_modules rather than in
# /node_modules.
RUN --mount=type=cache,target=/root/.cache/yarn \
    if compgen -G "src/plugins/*/package.json" > /dev/null; then \
        yarn install --pure-lockfile --modules-folder /node_modules; \
    fi

# dev target: deps installed, source mounted at runtime — no production build.
# Also installs the system libraries the Cypress test runner needs (GTK/X11
# runtime libs plus xvfb for a virtual display), so the webapp test suites can
# run inside the container.
FROM base AS dev
COPY --from=plugin-panels /webapp/src/plugins /opt/datalab-plugin-panels
# Add any nested plugin node_modules, as /app/src is bind-mounted at runtime
RUN cp -a /app/src/plugins/. /opt/datalab-plugin-panels/
COPY .docker/app_dev_entrypoint.sh /usr/local/bin/datalab-app-dev
RUN apt update \
    && apt install -y --no-install-recommends \
        libgtk2.0-0 \
        libgtk-3-0 \
        libgbm-dev \
        libnotify-dev \
        libnss3 \
        libxss1 \
        libasound2t64 \
        libxtst6 \
        xauth \
        xvfb \
    && rm -rf /var/lib/apt/lists/*

CMD [ "/bin/bash", "/usr/local/bin/datalab-app-dev" ]

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD node -e "fetch('http://localhost:8081').then(r => process.exit(r.ok ? 0 : 1)).catch(() => process.exit(1))"

# build target: runs the production Vite build. Derives from `base` rather
# than `dev` so production builds don't pull in the Cypress system libraries.
FROM base AS build

# Static deployment files are added in the production stage, so that changing them does
# not trigger a rebuild. Custom components are compiled into the bundle, so must stay here.
# This excludes the directory itself, as `public/custom/**` would still copy it empty, so
# adding the first static file to a deployment would trigger a rebuild.
COPY --exclude=public/custom --exclude=!public/custom/components/** webapp ./
COPY --from=plugin-panels /webapp/src/plugins ./src/plugins

# Deployment settings are not baked into the build: the entrypoint script writes
# them to `config.js` when the container starts, from `.env` files or an external
# docker-compose.
ENV NODE_ENV=production

RUN /node_modules/.bin/vite build

# production target: serves the compiled bundle with nginx, so no Node runtime
# or node_modules are needed in the final image. The entrypoint script writes
# the runtime `VUE_APP_*` settings to `config.js` before nginx starts.
FROM nginx:1.31.8-alpine AS production

EXPOSE 8081

RUN apk add --no-cache jq

COPY ./.docker/app/nginx.conf /etc/nginx/conf.d/default.conf
COPY --chmod=755 ./.docker/app_entrypoint.sh /docker-entrypoint.d/40-datalab-app-config.sh
COPY ./webapp/src/config.schema.json /app/config.schema.json
COPY --from=build /app/dist /app/dist

# The wildcard allows for `public/custom` not existing
COPY --exclude=components webapp/public/custo[m] /app/dist/custom/

# The version is written to `config.js` by the entrypoint script. Provided as a build arg
# so that neither the build layers nor the image depend on `.git`, and set here so that it
# does not invalidate the compiled bundle. Can be overridden when the container starts, by
# setting `VUE_APP_GIT_VERSION`. This uses a different name as Compose removes listed
# variables that are unset on the host, including those set by the image.
ARG VUE_APP_GIT_VERSION=0.0.0-git
ENV DATALAB_IMAGE_VERSION=${VUE_APP_GIT_VERSION}

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD wget -q --spider http://127.0.0.1:8081/ || exit 1
