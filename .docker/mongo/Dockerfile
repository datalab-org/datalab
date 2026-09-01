FROM mongo:8-noble
EXPOSE 27017
HEALTHCHECK --interval=30s --timeout=5s --start-interval=1s --start-period=180s --retries=3 CMD mongosh --quiet --eval "db.runCommand('ping').ok" || exit 1
