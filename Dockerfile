# syntax=docker/dockerfile:1
ARG BUILD_VERSION
#ARG PGID=1000
#ARG PUID=1000

# ************************************************************
# First stage: builder
# ************************************************************
FROM python:3.12 AS builder
# Make sure all messages always reach console
ARG BUILD_VERSION

# ******************************************
#           OpenTakServer Install
# ******************************************

# Set working directory
WORKDIR /app/

# Create and activate virtual environment
# Using final folder name to avoid path issues with packages
RUN python3 -m venv /app/.opentakserver_venv

# Enable venv
ENV PATH="/app/.opentakserver_venv/bin:$PATH"

# Install Opentakserver, if $BUILD_VERSION is not set, install latest
RUN pip3 install --no-cache-dir opentakserver${BUILD_VERSION:+==$BUILD_VERSION}

# ************************************************************
# Second stage: runtime
# ************************************************************
FROM python:3.12-slim AS runtime
ARG BUILD_VERSION

# Set environment variables
ENV DEBIAN_FRONTEND="noninteractive" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.opentakserver_venv/bin:$PATH" \
    HOME="/app"

LABEL maintainer="https://github.com/milsimdk"
LABEL org.opencontainers.image.title="Docker image for OpenTAKServer"
LABEL org.opencontainers.image.description="OpenTAKServer is yet another open source TAK Server for ATAK, iTAK, and WinTAK"
LABEL org.opencontainers.image.version="${BUILD_VERSION:-latest}"
LABEL org.opencontainers.image.authors="Brian - https://github.com/brian7704"
LABEL org.opencontainers.image.vendor="https://github.com/milsimdk"
LABEL org.opencontainers.image.source="https://github.com/milsimdk/ots-docker-image"
LABEL org.opencontainers.image.licenses="GNU General Public License v3.0"

# Copy opentakserver from build image
COPY --from=builder /app/.opentakserver_venv /app/.opentakserver_venv

# Fix bug https://github.com/brian7704/OpenTAKServer/issues/15
RUN pip3 uninstall -y bcrypt && pip3 install bcrypt==4.0.1

# Add Healthcheck for OTS
COPY --chmod=755 ./entrypoint.d/ /etc/entrypoint.d
COPY --chmod=755 ./healthcheck.py /app

HEALTHCHECK --interval=60s --start-period=30s CMD /app/healthcheck.py

# Flask will stop gracefully on SIGINT (Ctrl-C).
# Docker compose tries to stop processes using SIGTERM by default, then sends SIGKILL after a delay if the process doesn't stop.
STOPSIGNAL SIGINT

# 8081 OpenTAKServer
EXPOSE 8081/tcp

# 8088 TCP CoT streaming port
EXPOSE 8088/tcp

# 8089 SSL CoT streaming port
EXPOSE 8089/tcp

WORKDIR /app/ots

ENTRYPOINT [ "/etc/entrypoint.d/docker-entrypoint.sh" ]
CMD ["python3", "-m", "opentakserver.app"]
