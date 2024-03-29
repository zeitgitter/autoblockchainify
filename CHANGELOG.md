# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/) and this
project adheres to [Semantic Versioning](https://semver.org/).

# 1.0.1 - 2023-10-10

## Added

- Support
  [native `docker buildx` installs](https://docs.docker.com/engine/install/)

## Fixed

## Changed

- Updated Debian to `bookworm`
- Updated `zeitgitterd` to 1.1.6
- Updated `git timestamp` to 1.1.1 (through zeitgitterd)

# 1.0.0 - 2021-11-04

## Added

- Notice in `run.sh` that some `gpg` (_not_ `gpg1`) commands seem to remove the
  keys of the _PGP Digital Timestamping Service_ (probably due to their old
  format). If that happens, running
  `docker-compose exec --user 15177 autoblockchainify gpg1 --pgp2 --import /stamper.asc`
  will load the keys again.

## Fixed

## Changed

- Upgraded to debian:bullseye-slim

# 0.9.6 - 2021-06-25

## Added

- Name and print threads for debugging
- Allow additional daemon paramaters (e.g., `--debug-level XDEBUG`) to be passed
  to `make test`
- Additional debug level `XDEBUG` ("excessive debug"). If you want your
  configuration to be backward-compatible, do not use `--debug-level XDEBUG`,
  which will raise an exception at start of older versions, but
  `--debug-level 3`.
- Documentation for real-world mail test (and test for it)

## Fixed

- Spurious error message "Logfile vanished. Double mail receive thread?" was
  caused by too little wiggle room for timestamping+delays and bad logic
  (logfile creation wasn't the precondition for waiting for the mail). This
  resulted in every second mail-based timestamp being skipped for the example
  setup.
- Made mail logic more robust (see comment before `async_email_timestamp()`)

## Changed

- Commit messages now use "🔗" emoji directly instead of ":link:"
- Streamlined and improved logging messages; switched to Signale, using aligned
  mode (more readable without ANSI colors)
- Rely on `deltat` library instead of local copy
- No extra delay after last timestamper

# 0.9.5 - 2021-01-16

## Added

- Allow docker image to be built with a specific PyPI version (a feature you
  probably will not need, but is useful while developing/testing)
- Direct ability to run development docker

## Fixed

## Changed

- Version numbers of non-tagged versions now end in `.postX`, where `X` is the
  number of commits since the tag (unless overridden by `FORCE_VERSION`
  environment variable)
- Require `git timestamp` version of at least 1.0.4
- Docker image slightly smaller
- Docker processes run as user `blockchain` for more defensive security
- During a transition phase, there will be an ownership change for the
  `/blockchain` directory subtree (will be triggered if that directory is not
  writable by the user `blockchain`)

# 0.9.4 - 2020-12-09

## Added

- Documentation in the config files for `--zeitgitter-sleep`

## Fixed

- Copy-paste like rebase problems with `--zeitgitter-sleep`,
  `--push-repository`, and `--domain` leading to termination; releasing hotfix

## Changed

# 0.9.3 - 2020-12-09

## Added

- `--zeigitter-sleep` allows to sleep between upstream timestamps, e.g. to
  ensure a consistent ordering of cross-timestamping events for each commit.
- Time intervals (such as "5m3.5s") may skip the seconds indication, `s`. So
  `--zeigitter-sleep=0` is also valid.
- On restart, tries to resume waiting for a mail response from PGP Digital
  Timestamping Service (was added some versions ago, but never documented)
- Timespans may also indicate the number of weeks now (e.g., "1w 2d 8h 40m
  3.5s")
- Simplfied using multiple cross-timestampers:
  - Add support to push all branches using `--push_branch=*`, saving the need to
    list/update them all (see also _Changes_ below)
  - `--zeigitter-timestamp` no longer needs a branch name, if `git timestamp`
    will determine it correctly. This leads to much shorter and more
    maintainable lists of cross-timestamping servers.

## Fixed

- Docker health check failed due to missing `wget`

## Changed

- The interval defaults (10m with changes, at least once every 1h) in the
  configuration have been adopted to what is documented.
- Docker image is now based on `debian:buster-slim`. As the same number of
  packages (171) has to be added on top of it, starting with the smaller image
  is preferable. (See [#0.9.6---2020-08-13](v0.9.6 below) for why not using one
  of the `python` base images.)
- Default for `--push-branch` is now `*`, meaning `--all` (which cannot be
  expressed in the config file)

# 0.9.2 - 2020-10-02

## Added

- Suspend "normal" (non-forced) commits during merge, in order to not interfere
  with manual maintenance processes
- Prevent `git timestamp` > 1.0.3 from creating `~/.gitconfig`; instead, it will
  record key IDs in `~/.git/config`, keeping the blockchain cleaner

## Fixed

- Handle that `.gnupg` also is in the volume now
- Send out mail only every force interval. Also, do not trigger immediate
  addition of a mail reply only, avoiding double commits/timestamps every force
  interval on idle repositories.

## Changed

# 0.9.1 - 2020-09-27

## Added

- Support `.ssh` directory in the `blockchain` directory (not included in the
  Blockchain by default)

## Fixed

- `sample.env` now contains the actual names of the environment variables.
- Serialization for mail-related processing to avoid duplicate work and race
  conditions

## Changed

- Format of PGP Timestamper request mail message (ISO 8601 format)

# 0.9.0 - 2020-09-26

## Added

- Derived from Zeitgitter timestamping server

## Fixed

## Changed
