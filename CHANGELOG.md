# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/)
and this project adheres to [Semantic Versioning](https://semver.org/).


# 0.9.2+ - [Unreleased]
## Added
- On restart, tries to resume waiting for a mail response from PGP Digital
  Timestamping Service (was added some versions ago, but never documented)
- Timespans may also indicate the number of weeks now (e.g.,
  "1w 2d 8h 40m 3.5s")
- Simplfied using multiple cross-timestampers:
  * Add support to push all branches using `--push_branch=*`, saving the need
    to list/update them all (see also *Changes* below)
  * `--upstream-timestamp` no longer needs a branch name, if `git timestamp`
    will determine it correctly. This leads to much shorter and more
    maintainable lists of cross-timestamping servers.

## Fixed
- Docker health check failed due to missing `wget`

## Changed
- The interval defaults (10m with changes, at least once every 1h)
  in the configuration have been adopted to what is documented.
- Docker image is now based on `debian:buster-slim`. As the same number of
  packages (171) has to be added on top of it, starting with the smaller image
  is preferable. (See [#0.9.6---2020-08-13](v0.9.6 below) for why not using one
  of the `python` base images.)
- Default for `--push-branch` is now `*`, meaning `--all` (which cannot be
  expressed in the config file)
- `ZEITGITTER_FAKE_TIME` (needed only for tests) is removed from the
  environment of `git timestamp` clients that connect to cross-timestamping
  servers specified as server name only (as opposed to `branch=server` tuples)
  to allow both testing against our local timeserver (which does not use wall
  clock to achieve reproducible signatures) and against real-world timeservers
  obeying wall clock.


# 0.9.2 - 2020-10-02
## Added
- Suspend "normal" (non-forced) commits during merge, in order to not
  interfere with manual maintenance processes
- Prevent `git timestamp` > 1.0.3 from creating `~/.gitconfig`; instead, it
  will record key IDs in `~/.git/config`, keeping the blockchain cleaner

## Fixed
- Handle that `.gnupg` also is in the volume now
- Send out mail only every force interval. Also, do not trigger immediate
  addition of a mail reply only, avoiding double commits/timestamps every
  force interval on idle repositories.

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
