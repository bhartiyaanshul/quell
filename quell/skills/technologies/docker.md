---
name: docker
category: technologies
description: Docker image build failures, runtime errors, and container networking issues
applicable_when:
  - tech_stack_includes: "docker"
  - error_contains: "docker"
  - error_contains: "exec format error"
  - error_contains: "no such file or directory"
  - error_contains: "cannot connect to the Docker daemon"
  - error_contains: "manifest unknown"
  - error_contains: "pull access denied"
  - error_contains: "Error response from daemon"
severity_hint: medium
---

# Docker incident cheatsheet

## Where to look first
- **`docker ps -a`** — is the container actually running? "Exited
  (1) 3 seconds ago" is common immediately after `docker run`.
- **`docker logs <container>`** — last-ditch stdout + stderr, even
  for exited containers. Add `--tail 100 --follow` for live.
- **`docker inspect <container>`** — full JSON. The `State` block
  includes `ExitCode`, `OOMKilled`, `Error`, and the command actually
  executed.

## Common failure shapes
- **`exec format error`.** You built for the wrong architecture.
  Happens a lot when Apple Silicon devs push images that the Linux
  x86_64 runner then pulls. Fix by building multi-arch:
  `docker buildx build --platform linux/amd64,linux/arm64 -t ... --push .`
- **`no such file or directory`** on a path you know exists.
  Usually a `COPY` step missed the file (bad path, outside build
  context, excluded by `.dockerignore`). Shell into the image:
  `docker run --rm -it <image> sh` and `ls` around.
- **`cannot connect to the Docker daemon`.** Docker Desktop is not
  running, or the current user isn't in the `docker` group on
  Linux, or `DOCKER_HOST` is set to something dead.
- **`manifest unknown` / `pull access denied`.** Tag doesn't exist,
  or the registry is private and you're not logged in. `docker login
  <registry>` first.
- **Container gets `OOMKilled`.** Docker's `--memory` limit (or
  Compose's `deploy.resources.limits.memory`) is tighter than the
  app needs. `docker stats` shows live usage.
- **Networking: app inside container can't reach host DB.** On
  macOS / Windows use `host.docker.internal`. On Linux, add
  `--add-host=host.docker.internal:host-gateway` to the run command.

## Useful commands
- `docker system df` — how much space images / containers / volumes
  / build cache are taking. `docker system prune -af --volumes`
  reclaims it.
- `docker history <image>` — every layer with its size + command.
  Useful for spotting bloat and for cache-bust diagnosis.
- `docker exec -it <container> sh` — shell into a running container
  without stopping it.
- `docker events --since 10m` — real-time stream of daemon events.
  Useful when containers are disappearing "for no reason".
