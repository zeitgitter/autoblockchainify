# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/)
and this project adheres to [Semantic Versioning](https://semver.org/).


# 0.9.2+ - [Unreleased]
## Added

## Fixed
- Docker health check failed due to missing `wget`

## Changed
- The interval defaults (10m with changes, at least once every 1h)
  in the configuration have been adopted to what is documented.


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
