ARG UV_VERSION="0.9.21"
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv_image

FROM python:3.11-slim-trixie AS api
ARG TARGETARCH
SHELL ["/bin/bash", "--login", "-c"]

# Useful for installing deps from git, preventing big downloads and bandwith quotas
ENV GIT_LFS_SKIP_SMUDGE=1

# Install system dependencies
RUN apt update && apt install -y git gnupg curl tree mdbtools && apt clean

# Install MongoDB tools in the official way
WORKDIR /opt

RUN if [ "$TARGETARCH" = "arm64" ]; then \
      ARCH="arm64"; \
    else \
      ARCH="x86_64"; \
    fi && \
    curl -fsSL https://fastdl.mongodb.org/tools/db/mongodb-database-tools-ubuntu2204-${ARCH}-100.9.0.deb -o mongodb-tools.deb && \
    apt update && \
    (apt install -y ./mongodb-tools.deb || apt --fix-broken install -y) && \
    rm -f mongodb-database-tools-*.deb && \
    apt clean &&  \
    mongodump --help

COPY --from=uv_image /uv /usr/local/bin/uv
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/.venv \
    UV_PYTHON=python3.11

# Used to fake the version of the package in cases where datalab is only
# available as a git submodule or worktree
ARG SETUPTOOLS_SCM_PRETEND_VERSION
ENV SETUPTOOLS_SCM_PRETEND_VERSION=${SETUPTOOLS_SCM_PRETEND_VERSION}

WORKDIR /app
COPY ./pydatalab/pyproject.toml .
COPY ./pydatalab/uv.lock .
COPY ./pydatalab/plugins/ ./plugins

RUN uv sync --locked --no-dev --all-extras

WORKDIR /app

# Install the local version of the package and mount the repository data to get version info
COPY ./pydatalab/ ./
RUN git config --global --add safe.directory /

# Install editable mode so that the server runs from a sensible place where we can stuff .env files
RUN --mount=type=bind,target=/.git,source=./.git uv pip install --python /opt/.venv/bin/python --no-deps --editable .

# Define some default gunicorn runtime args
ENV WEB_CONCURRENCY=4
ENV GUNICORN_CMD_ARGS="--preload --timeout 120 --graceful-timeout 90"
ENV PORT=5001

CMD ["/bin/bash", "-c", "/opt/.venv/bin/python -m gunicorn -b 0.0.0.0:${PORT} -w ${WEB_CONCURRENCY} ${GUNICORN_CMD_ARGS} 'pydatalab.main:create_app()'"]

HEALTHCHECK --interval=30s --timeout=30s --start-interval=15s --start-period=30s --retries=3 CMD curl --fail http://localhost:${PORT}/healthcheck/is_ready || exit 1
