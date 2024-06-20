# Docker image for OpenTAKServer
---

### NOT READY FOR PRODUCTION YET

---

Used here: https://github.com/milsimdk/ots-docker

### Requirements
 - Docker must be installed
 - Docker compose v2 is used
 - Platform support: linux/amd64, linux/arm64

### Build arguments defaults
```Dockerfile
ARG BUILD_VERSION
ARG PGID=1000
ARG PUID=1000
```

### Thanks
  - [Brian](https://github.com/brian7704) for creating [OpenTAKServer](https://github.com/brian7704/OpenTAKServer)
