#!/bin/bash -e
# Usage: migrate.sh <USER> <DIR> <CMD>
# Run ownership migration if DIR not writable by USER,
# then drop privileges and continue to CMD

# Set up environment
export USER="$1"
export HOME="$2"
shift 2

# `--inh-caps=-all` is fragile, see e.g. https://bugs.archlinux.org/task/67781
#setpriv="setpriv --reuid $USER --regid $USER --init-groups --inh-caps=-all --no-new-privs"

# Migrate
su $USER -c "test -w $HOME" || chown -R $USER:$USER $HOME

# Continue unprivileged
exec su $USER -c "$*"
