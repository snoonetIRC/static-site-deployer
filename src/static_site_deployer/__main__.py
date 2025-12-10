# SPDX-FileCopyrightText: 2019-present Snoonet
#
# SPDX-License-Identifier: MIT

"""Main entrypoint for static-site-deployer."""

if __name__ == "__main__":
    import sys

    from static_site_deployer.cli import cli

    sys.exit(cli())
