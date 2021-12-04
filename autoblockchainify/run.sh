#!/bin/sh -e
# Docker runner

# This needs to go *into* the volume, which is probably mapped by
# docker-compose. So at start only… (as opposed to image creation)
# NOTE: Some `gpg` commands (*not* `gpg1`) seem to remove these
# old keys; you may need to re-import the keys manually then.
if [ ! -d /blockchain/.gnupg/ ]; then
  gpg1 --pgp2 --import /stamper.asc
fi
exec autoblockchainify "$@"
