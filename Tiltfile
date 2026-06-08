# Tiltfile — local dev orchestration
# Run with: tilt up

docker_compose("docker/docker-compose.yml")

dc_resource("frontend", labels=["app"])
dc_resource("backend", labels=["app"])
