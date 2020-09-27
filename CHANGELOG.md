# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/)
and this project adheres to [Semantic Versioning](https://semver.org/).


# 0.9.1+ - [Unreleased]
## Added

## Fixed
- Handle that `.gnupg` also is in the volume now

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
