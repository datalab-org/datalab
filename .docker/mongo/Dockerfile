# MONGO_IMAGE_TAG allows CI to override the MongoDB version: recent 8.x releases refuse to
# start on Linux kernels 6.19--7.0.13 (https://jira.mongodb.org/browse/SERVER-125742)
ARG MONGO_IMAGE_TAG=8-noble
FROM mongo:${MONGO_IMAGE_TAG}
# Refresh the system CA store on top of the base image
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*
EXPOSE 27017
HEALTHCHECK --interval=30s --timeout=5s --start-interval=1s --start-period=180s --retries=3 CMD mongosh --quiet --eval "db.runCommand('ping').ok" || exit 1
