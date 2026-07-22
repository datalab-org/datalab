# syntax=docker/dockerfile:1
FROM node:22.22-bullseye-slim AS build
SHELL ["/bin/bash", "--login", "-c"]

WORKDIR /app

EXPOSE 8081

RUN apt update && apt install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

COPY webapp/package.json webapp/yarn.lock ./

# Using a custom node_modules location to avoid mounting it outside of docker
RUN --mount=type=cache,target=/root/.cache/yarn yarn install --frozen-lockfile --modules-folder /node_modules

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
ARG VUE_APP_ENABLE_LOGIN_PAGE=magic-enable-login-page
ARG VUE_APP_LOGIN_HIDE_UNAVAILABLE_AUTH=magic-login-hide-unavailable-auth
# Version source for scripts/get-version.js. Provided as a build arg so the
# build layer doesn't depend on `.git` (which would invalidate cache every commit).
ARG VUE_APP_GIT_VERSION=0.0.0+ci
ENV VUE_APP_GIT_VERSION=${VUE_APP_GIT_VERSION}

COPY webapp ./
RUN /node_modules/.bin/vue-cli-service build

FROM node:22.22-bullseye-slim AS production

ENV PATH=$PATH:/node_modules/.bin
COPY ./.docker/app_entrypoint.sh /app/

COPY webapp/package.json webapp/yarn.lock ./

COPY --from=build /app/dist /app/dist
RUN --mount=type=cache,target=/root/.cache/yarn yarn install --frozen-lockfile --modules-folder /node_modules --production

CMD [ "/bin/bash", "-c", "/app/app_entrypoint.sh" ]

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD node -e "fetch('http://localhost:8081').then(r => process.exit(r.ok ? 0 : 1)).catch(() => process.exit(1))"
