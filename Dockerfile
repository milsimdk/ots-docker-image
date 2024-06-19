# syntax=docker/dockerfile:1
ARG BUILD_VERSION
ARG PGID=1000
ARG PUID=1000

# ************************************************************
# First stage: builder
# ************************************************************
FROM python:3.12 AS builder
ARG BUILD_VERSION

# Make sure all messages always reach console
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app/

# Create and activate virtual environment
# Using final folder name to avoid path issues with packages
RUN python3 -m venv /app/.opentakserver_venv
# Enable venv
ENV PATH="/app/.opentakserver_venv/bin:$PATH"

# Install Opentakserver
RUN pip3 install --no-cache-dir opentakserver==${BUILD_VERSION}

# ************************************************************
# Second stage: runtime
# ************************************************************
FROM python:3.12-slim AS runtime
ARG BUILD_VERSION
ARG PGID
ARG PUID

# Make sure all messages always reach console
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Activate virtual environment
ENV PATH="/app/.opentakserver_venv/bin:$PATH"

LABEL maintainer="https://github.com/milsimdk"
LABEL org.opencontainers.image.title="Docker image for OpenTAKServer"
LABEL org.opencontainers.image.description="OpenTAKServer is yet another open source TAK Server for ATAK, iTAK, and WinTAK"
LABEL org.opencontainers.image.version="${BUILD_VERSION}"
LABEL org.opencontainers.image.authors="Brian - https://github.com/brian7704"
LABEL org.opencontainers.image.vendor="https://github.com/milsimdk"
LABEL org.opencontainers.image.source="https://github.com/milsimdk/ots-docker-image"
LABEL org.opencontainers.image.licenses="GNU General Public License v3.0"

# Create OTS user
RUN groupadd -g ${PGID:-1000} -r ots && \
    useradd -u ${PUID:-1000} -g ${PGID:-1000} -m -d /app ots && \
    mkdir /app/ots/ &&  chown -R ots:ots /app

# Set working directory
WORKDIR /app/ots

# Copy opentakserver from build image
COPY --from=builder /app/.opentakserver_venv /app/.opentakserver_venv

RUN pip3 uninstall -y bcrypt && pip3 install bcrypt==4.0.1

# Add Healthcheck for OTS
COPY __init__.py healthcheck.py /app/scripts/
RUN chmod +x /app/scripts/*

#HEALTHCHECK --interval=1m --start-period=1m CMD python3 /app/scripts/healthcheck.py

# Run as OTS user
USER ots

# Flask will stop gracefully on SIGINT (Ctrl-C).
# Docker compose tries to stop processes using SIGTERM by default, then sends SIGKILL after a delay if the process doesn't stop.
STOPSIGNAL SIGINT

# 8081 OpenTAKServer
EXPOSE 8081/tcp

# 8088 TCP CoT streaming port
EXPOSE 8088/tcp

# 8089 SSL CoT streaming port
EXPOSE 8089/tcp

#ENTRYPOINT [ "python3" ]
CMD [ "python3", "/app/scripts/__init__.py" ]
