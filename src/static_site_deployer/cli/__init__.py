# SPDX-FileCopyrightText: 2019-present Snoonet
#
# SPDX-License-Identifier: MIT

"""CLI for static-site-deployer."""

import re
import sys
import tarfile
from pathlib import Path
from shutil import rmtree
from typing import Annotated

import click
import requests
import typer
from github import Github
from github.GitRelease import GitRelease
from github.GitReleaseAsset import GitReleaseAsset

ASSET_ID_FILE = ".asset_id"
CURRENT_PATH = "current"
HISTORY_COUNT = 5
RELEASES_PATH = "releases"
RELEASE_PREFIX = "website-v"

RELEASE_URL = "https://api.github.com/repos/{repo}/releases"

gh = Github()


def _release_filter(release: GitRelease) -> bool:
    return not release.draft and not release.prerelease and bool(release.assets)


def _get_latest_release_asset(repo: str) -> GitReleaseAsset:
    releases = gh.get_repo(repo).get_releases()
    release = next(filter(_release_filter, releases), None)

    if release is None:
        msg = "Unable to find matching release"
        raise ValueError(msg)

    return release.assets[0]


def _check_for_update(repo: str, deploy_path: Path) -> None:
    if not deploy_path.is_dir():
        sys.exit("Website not deployed")

    asset_id_file = deploy_path / CURRENT_PATH / ASSET_ID_FILE
    if not asset_id_file.exists():
        sys.exit("No assets currently deployed")

    current_id = asset_id_file.read_text().strip()
    if not current_id:
        sys.exit("No assets currently deployed")

    asset = _get_latest_release_asset(repo)
    if str(asset.id) != current_id:
        sys.exit("Assets out of date")

    sys.exit(0)


Version = tuple[int, int, int]
version_re = re.compile(r"(\d+)\.(\d+)\.(\d+)")


def _parse_version(version: str) -> Version:
    match = version_re.fullmatch(version)
    if match is None:
        msg = f"Can't parse version: {version}"
        raise ValueError(msg)

    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def _do_cleanup(releases_dir: Path) -> None:
    directories = list(releases_dir.glob(f"{RELEASE_PREFIX}*"))

    if len(directories) <= HISTORY_COUNT:
        click.echo("Did not run clean up (too few historic releases)")
        return

    def key(d: Path) -> Version:
        return _parse_version(d.name.replace(RELEASE_PREFIX, ""))

    directories.sort(key=key, reverse=True)

    to_remove = directories[HISTORY_COUNT:]
    for directory in to_remove:
        rmtree(releases_dir / directory)

    if to_remove:
        click.echo(f"Cleaned up {len(to_remove)} historic releases")
    else:
        click.echo("No clean up required")


def _do_update(repo: str, deploy_path: Path) -> None:
    releases_dir = deploy_path / RELEASES_PATH
    current_link = deploy_path / CURRENT_PATH

    asset = _get_latest_release_asset(repo)

    # Requires that the asset be '<name>.tar.gz'
    release_name = asset.name.rsplit(".", 2)[0]

    release_dir = releases_dir / release_name
    if not release_dir.exists():
        release_dir.mkdir(parents=True)

    with (
        requests.get(
            asset.url,
            stream=True,
            headers={"Accept": "application/octet-stream"},
            timeout=30,
        ) as response,
        tarfile.open(fileobj=response.raw, mode="r|*") as tarball,
    ):
        tarball.extractall(  # noqa: S202 # This tarball is trusted as we are making this ourselves
            path=str(release_dir)
        )

    # Record the ID of this asset for later update checks
    (release_dir / ASSET_ID_FILE).write_text(f"{asset.id}")

    if current_link.is_symlink():
        current_link.unlink()

    current_link.symlink_to(release_dir, target_is_directory=True)
    click.echo(f"Deployed {release_name}")

    _do_cleanup(releases_dir)


cli = typer.Typer()

DeployPath = Annotated[
    Path,
    typer.Argument(
        file_okay=False,
        dir_okay=True,
        writable=True,
        readable=True,
        resolve_path=False,
    ),
]


@cli.command()
def check(repo: Annotated[str, typer.Argument()], path: DeployPath) -> None:
    """Check if deployment is up-to-date.

    Arguments:
        repo: GitHub repository to download from
        path: Where to deploy the site
    """
    _check_for_update(repo, path)


@cli.command()
def update(repo: Annotated[str, typer.Argument()], path: DeployPath) -> None:
    """Update deployment.

    Arguments:
        repo: GitHub repository to download from
        path: Where to deploy the site
    """
    _do_update(repo, path)
