from qtile_lxa import widget


docker_widget = widget.DockerCompose(
    config=widget.DockerComposeConfig(
        compose_file="docker-compose.yml",
    )
)
