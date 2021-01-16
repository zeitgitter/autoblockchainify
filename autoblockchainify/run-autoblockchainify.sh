#!/bin/sh -e
# Docker runner

# This needs to go *into* the volume, which is probably mapped by
# docker-compose. So at start only… (as opposed to image creation)
if [ ! -d /blockchain/.gnupg/ ]; then
  gpg1 --pgp2 --import /root/stamper.asc
fi
exec autoblockchainify "$@"
