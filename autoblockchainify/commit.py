#!/usr/bin/python3
#
# autoblockchainify — Turn a directory into a GIT Blockchain
#
# Copyright (C) 2019,2020 Marcel Waldvogel
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

# Committing to git and obtaining timestamps

from datetime import datetime, timezone
import logging as _logging
from pathlib import Path
import subprocess
import sys
import threading
import time
import traceback

import pygit2 as git

import autoblockchainify.config
import autoblockchainify.mail

logging = _logging.getLogger('commit')


def push_upstream(repo, to, branches):
    logging.info("Pushing to %s" % (['git', 'push', to] + branches))
    ret = subprocess.run(['git', 'push', to] + branches,
                         cwd=repo)
    if ret.returncode != 0:
        logging.error("'git push %s %s' failed" % (to, ' '.join(branches)))


def cross_timestamp(repo, options):
    ret = subprocess.run(['git', 'timestamp'] + options, cwd=repo)
    if ret.returncode != 0:
        sys.stderr.write("git timestamp %s failed" % (' '.join(options)))


def has_user_changes(repo):
    """Check whether there are uncommitted changes, i.e., whether
    `git status -z` has any output. A modification of only `pgp-timestamp.sig`
    is ignored, as it is neither necessary nor desirable to trigger on it:
    (a) our own timestamp is not really needed on it and
    (b) it would cause an unnecessary second timestamp per idle force period."""
    ret = subprocess.run(['git', 'status', '-z'],
                         cwd=repo, capture_output=True, check=True)
    return len(ret.stdout) > 0 and ret.stdout != b' M pgp-timestamp.sig\0'


def pending_merge(repo):
    """Check whether there is a pending merge."""
    return Path(repo, '.git', 'MERGE_HEAD').is_file()


def commit_current_state(repo):
    """Force a commit; will be called only if a commit has to be made.
    I.e., if there really are changes or the force duration has expired."""
    now = datetime.now(timezone.utc)
    nowstr = now.strftime('%Y-%m-%d %H:%M:%S UTC')
    subprocess.run(['git', 'add', '.'],
                   cwd=repo, check=True)
    subprocess.run(['git', 'commit', '--allow-empty',
                    '-m', ":link: Autoblockchainify data as of " + nowstr],
                   cwd=repo, check=True)


def head_older_than(repo, duration):
    """Check whether the last commit is older than `duration`.
    Unborn HEAD is *NOT* considered to be older; as a result,
    the first commit will be done only after the first change."""
    r = git.Repository(repo)
    if r.head_is_unborn:
        return False
    now = datetime.utcnow()
    return datetime.utcfromtimestamp(
        r.head.peel().commit_time) + duration < now


def do_commit():
    """To be called in a non-daemon thread to reduce possibilities of
    early termination.

    1. Commit if
       * there is anything uncommitted, or
       * more than FORCE_AFTER_INTERVALS intervals have passed since the
         most recent commit.
       * Normal (non-forced) commits are suspended while a merge (=manual)
         operation is in progress.
    2. Timestamp using HTTPS (synchronous)
    3. (Optionally) push
    4. (Optionally) cross-timestamp using email (asynchronous), if the previous
       email has been sent more than FORCE_AFTER_INTERVALS ago. The response
       will be added to a future commit."""
    # Allow 5% of an interval tolerance, such that small timing differences
    # will not lead to lengthening the duration by one commit_interval
    force_interval = (autoblockchainify.config.arg.commit_interval
                      * (autoblockchainify.config.arg.force_after_intervals - 0.05))
    try:
        repo = autoblockchainify.config.arg.repository
        # If a merge (a manual process on the repository) is detected,
        # try to not interfere with the manual process and wait for the
        # next forced update
        if ((has_user_changes(repo) and not pending_merge(repo))
                or head_older_than(repo, force_interval)):
            # 1. Commit
            commit_current_state(repo)

            # 2. Timestamp (synchronously) using Zeitgitter
            repositories = autoblockchainify.config.arg.push_repository
            branches = autoblockchainify.config.arg.push_branch
            for r in autoblockchainify.config.arg.zeitgitter_servers:
                logging.info("Cross-timestamping %s" % r)
                if '=' in r:
                    (branch, server) = r.split('=', 1)
                    cross_timestamp(repo, ['--branch', branch,
                        '--server', server])
                else:
                    cross_timestamp(repo, ['--server', r])
                time.sleep(autoblockchainify.config.arg.zeitgitter_sleep.total_seconds())

            # 3. Push
            for r in repositories:
                logging.info("Pushing upstream to %s" % r)
                push_upstream(repo, r, branches)

            # 4. Timestamp by mail (asynchronously)
            if autoblockchainify.config.arg.stamper_own_address:
                autoblockchainify.mail.async_email_timestamp(wait=force_interval)

        logging.info("do_commit done")
    except Exception as e:
        logging.error("Unhandled exception in do_commit() thread: %s: %s" %
                      (e, ''.join(traceback.format_tb(sys.exc_info()[2]))))


def loop():
    """Run at given interval and offset"""
    interval = autoblockchainify.config.arg.commit_interval.total_seconds()
    offset = autoblockchainify.config.arg.commit_offset.total_seconds()
    while True:
        now = time.time()
        until = now - (now % interval) + offset
        if until <= now:
            until += interval
        time.sleep(until - now)
        threading.Thread(target=do_commit, daemon=False).start()
