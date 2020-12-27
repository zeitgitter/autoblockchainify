# For development docker builds, install from local package instead from PyPI.
# For this, `##DEVONLY##` strings at the start of the line will be removed for
# the dev build Dockerfile, whereas lines ending in `##PRODONLY##` will be
# deleted.

FROM debian:buster-slim

# The next line is hardcoded in Makefile as PRODONLY,
# as ARG does not support comments
ARG VERSIONMATCH=

# gnupg1/gpg1 steps are for interfacing with the PGP Timestamping Service only.
# Explicit python3-pygit2 install is required for ARMv6 only.
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
RUN pip3 install autoblockchainify${VERSIONMATCH} ##PRODONLY##
##DEVONLY## COPY autoblockchainify-*.whl /root/
##DEVONLY## RUN pip3 install /root/autoblockchainify-*.whl

# Ensure SSH keys also survive an update
# `usermod --home /blockchain root` refuses, as there are running procs
RUN sed 's,:/root:,:/blockchain:,' < /etc/passwd > /etc/passwd+ && \
    mv /etc/passwd+ /etc/passwd

# Import (old-style) PGP key for PGP Digital Timestamping Service, so it is
# ready if anyone wants to use it
COPY stamper.asc /root/
COPY run-autoblockchainify.sh health.sh /
RUN mkdir /blockchain

# Runtime settings
# Prevent `git timestamp` from creating `~/.gitconfig`
ENV FORCE_GIT_REPO_CONFIG=1
CMD ["/run-autoblockchainify.sh", "--repository", "/blockchain"]
HEALTHCHECK --timeout=3s CMD ["/health.sh"]
