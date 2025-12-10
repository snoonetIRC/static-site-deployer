# SPDX-FileCopyrightText: 2019-present Snoonet
#
# SPDX-License-Identifier: MIT

"""Test CLI."""

from static_site_deployer.cli import cli


def test_cmd() -> None:
    """Ensure commands are registered successfully."""
    assert len(cli.registered_commands) == 2
