# static-site-deployer

Scripts for managing deployment of snoonetIRC/static-web. No GitHub credentials
are required as only the public API is used.

## Check release status

Uses the public GitHub API to list available releases, and checks whether the
latest release is installed in the provided directory.

```
python3 updater.py check snoonetIRC/static-web path/to/website/dir
```

## Update release

Attempts to download the most recent release into the provided directory. Also
cleans up all but the five most recent releases from the directory.

```
python3 updater.py update snoonetIRC/static-web path/to/website/dir
```

