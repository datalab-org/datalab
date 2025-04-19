# syntax=docker/dockerfile:1
FROM node:20-bullseye AS build
SHELL ["/bin/bash", "--login", "-c"]

WORKDIR /app

EXPOSE 8081

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

COPY webapp ./
RUN --mount=type=bind,target=/.git,src=./.git VUE_APP_GIT_VERSION=$(node scripts/get-version.js) /node_modules/.bin/vue-cli-service build

FROM node:20-bullseye AS production

ENV PATH=$PATH:/node_modules/.bin
COPY ./.docker/app_entrypoint.sh /app/

COPY webapp/package.json webapp/yarn.lock ./

COPY --from=build /app/dist /app/dist
RUN --mount=type=cache,target=/root/.cache/yarn yarn install --frozen-lockfile --modules-folder /node_modules --production

CMD [ "/bin/bash", "-c", "/app/app_entrypoint.sh" ]

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD curl --fail http://localhost:8081 || exit 1
