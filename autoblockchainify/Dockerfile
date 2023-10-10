# For development docker builds, install from local package instead from PyPI.
# For this, `##DEVONLY##` strings at the start of the line will be removed for
# the dev build Dockerfile, whereas lines ending in `##PRODONLY##` will be
# deleted.

FROM debian:bookworm-slim

# The next line is hardcoded in Makefile as PRODONLY,
# as ARG does not support comments
ARG VERSIONMATCH=

# gnupg1/gpg1 steps are for interfacing with the PGP Timestamping Service only.
RUN apt update && \
    apt install -y gnupg1 libgit2-dev python3-pygit2 python3-pip git wget && \
    apt clean && \
    rm -rf /var/lib/apt/lists

# Verify that OS packages, Python version and Python package can interoperate
# (apt libgit2+python3-pygit2 with Python interpreter, pip pygit2)
RUN python3 -c "import pygit2"

# Provide `--build-arg VERSIONMATCH===0.9.4` or similar to ask
# for a specific version (instead of `==`, also other comparison
# operators could be used.
RUN pip3 install --break-system-packages autoblockchainify${VERSIONMATCH} ##PRODONLY##
##DEVONLY## COPY autoblockchainify-*.whl /root/
##DEVONLY## RUN pip3 install --break-system-packages /root/autoblockchainify-*.whl

# Run as non-root (which also ensures SSH keys survive an update)
# Use an empty home, not populated with /etc/skel.
RUN useradd --home-dir /blockchain --create-home --skel /does/not/exist --uid 15177 blockchain

# Import (old-style) PGP key for PGP Digital Timestamping Service, so it is
# ready if anyone wants to use it
COPY stamper.asc migrate.sh run.sh health.sh /

# Runtime settings
# Prevent `git timestamp` from creating `~/.gitconfig`
ENV FORCE_GIT_REPO_CONFIG=1

# Run the start script as root during a transition phase, so
# ownership migration can be performed.
CMD ["/migrate.sh", "blockchain", "/blockchain", "/run.sh", "--repository", "/blockchain"]
# `USER` applies to all commands executed after the directive, so it applies to
# `CMD`, even if `CMD` is above. So have to disable it during migration.
#USER blockchain
HEALTHCHECK --timeout=3s CMD ["su", "blockchain", "/health.sh"]
