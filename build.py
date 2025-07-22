#!/usr/bin/env python3
import requests
import subprocess
import typing

DOCKER_IMAGE: typing.Final[str] = "vijaysharma4/chipyard-image"
DOCKERFILE: typing.Final[str] = "Dockerfile"
GITHUB_REPO: typing.Final[str] = "ucb-bar/chipyard"


def run(cmd: str) -> None:
    subprocess.run(cmd, shell=True, check=True)


def get_github_release_tags() -> typing.Sequence[str]:
    tags: typing.List[str] = []
    page = 1

    while True:
        response = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/releases?page={page}")
        response.raise_for_status()
        data = response.json()
        if not data:
            break
        for release in data:
            tags.append(release.tag_name)
        page += 1

    return tags


def get_github_commit_sha(tag: str) -> str:
    response1 = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/git/ref/tags/{tag}")
    response1.raise_for_status()
    data = response1.json()

    response2 = requests.get(data["object"]["url"])
    response2.raise_for_status()
    obj = response2.json()

    if obj["type"] == "tag":
        response3 = requests.get(obj["object"]["url"])
        response3.raise_for_status()
        return response3.json()["sha"]

    return obj["sha"]


def docker_tag_exists(tag: str) -> bool:
    return requests.get(f"https://hub.docker.com/v2/repositories/{DOCKER_IMAGE}/tags/{tag}").status_code == 200


def build_and_push_image( tag: str, commit_hash: str) -> None:
    tag_name = f"{DOCKER_IMAGE}:{tag}"
    run(f"podman build -f {DOCKERFILE} -t {tag_name} --build-arg COMMIT={commit} .")
    run(f"podman push {tag_name}")


def build_and_push_latest() -> None:
    response = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/commits")
    response.raise_for_status()
    build_and_push_image("latest", response.json()[0]["sha"])


def main():
    run("podman login docker.io")

    for tag in get_github_release_tags(GITHUB_REPO):
        if docker_tag_exists(tag):
            print(f"{tag} already published; skipping")
        else:
            print(f"Building and pushing {tag}")
            sha = get_github_commit_sha(GITHUB_REPO, tag)
            build_and_push_image(tag, sha)

    print("Building and pushing latest")
    build_and_push_latest()


if __name__ == "__main__":
    main()
