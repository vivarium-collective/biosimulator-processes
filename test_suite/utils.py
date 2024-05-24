import docker
import docker.errors
from docker.models.images import Image


def get_docker_image(docker_client: docker.client.DockerClient, tag: str, pull: bool = True) -> Image:
    """ Get a Docker image for a simulator

    Args:
        docker_client (:obj:`docker.client.DockerClient`): Docker client
        tag (:obj:`str`): tag (e.g., ``biosimulators/tellurium``) or
            URL (``ghcr.io/biosimulators/tellurium``) for a Docker image of a simulator
        pull (:obj:`bool`, optional): whether to pull the image from Docker

    Returns:
        :obj:`docker.models.images.Image`: Docker image
    """
    image: Image
    try:
        image = docker_client.images.get(tag)
        if pull:
            try:
                image = docker_client.images.pull(tag)
            except Exception:  # pragma: no cover
                pass
    except Exception:
        if pull:
            try:
                image = docker_client.images.pull(tag)
            except Exception:
                raise docker.errors.ImageNotFound("Image '{}' for simulator could not be pulled".format(tag))
        else:
            raise docker.errors.ImageNotFound("Image '{}' for simulator is not available locally".format(tag))

    return image
