#!/usr/bin/python3
#
# autoblockchainify — Turn a directory into a GIT Blockchain
#
# Copyright (C) 2019-2021 Marcel Waldvogel
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

# Sending and receiving mail

import signale
import os
import re
import subprocess
import threading
import time
from datetime import datetime, timedelta
from imaplib import IMAP4
from pathlib import Path
from smtplib import SMTP
from time import gmtime, strftime

import pygit2 as git

import autoblockchainify.config

logging = signale.Signale({"scope": "mail"})
serialize_receive = threading.Lock()
serialize_create = threading.Lock()


def split_host_port(host, default_port):
    if ':' in host:
        host, port = host.split(':', 1)
        return (host, int(port))
    else:
        return (host, default_port)


def send(body, subject='Stamping request', to=None):
    # Does not work in unittests if assigned in function header
    # (are bound too early? At load time instead of at call time?)
    if to is None:
        to = autoblockchainify.config.arg.stamper_to
    (host, port) = split_host_port(
        autoblockchainify.config.arg.stamper_smtp_server, 587)
    with SMTP(host, port=port) as smtp:
        smtp.starttls()
        smtp.login(autoblockchainify.config.arg.stamper_username,
                   autoblockchainify.config.arg.stamper_password)
        frm = autoblockchainify.config.arg.stamper_own_address
        date = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
        msg = """From: %s
To: %s
Date: %s
Subject: %s

%s""" % (frm, to, date, subject, body)
        smtp.sendmail(frm, to, msg)
        logging.complete("Timestamping request mailed")


def extract_pgp_body(body):
    try:
        body = str(body, 'ASCII')
    except TypeError as t:
        logging.warning("Conversion error for message body: %s" % t)
        return None
    lines = body.splitlines()
    start = None
    for i in range(0, len(lines)):
        if lines[i] == '-----BEGIN PGP SIGNED MESSAGE-----':
            logging.debug("Found start at line %d: %s" % (i, lines[i]))
            start = i
            break
    else:
        return None

    end = None
    for i in range(start, len(lines)):
        if lines[i] == '-----END PGP SIGNATURE-----':
            logging.debug("Found end at line %d: %s" % (i, lines[i]))
            end = i
            break
    else:
        return None
    return lines[start:end + 1]


def save_signature(bodylines, logfile):
    logging.xdebug("save_signature()")
    repo = autoblockchainify.config.arg.repository
    ascfile = Path(repo, 'pgp-timestamp.sig')
    with ascfile.open(mode='w') as f:
        f.write('\n'.join(bodylines) + '\n')
        # Change will be picked up by next check for directory modification
    logfile.unlink()  # Mark as reply received, no need for resumption


def maybe_decode(s):
    """Decode, if it is not `None`"""
    if s is None:
        return s
    else:
        return s.decode('ASCII')


def body_signature_correct(bodylines, stat):
    body = '\n'.join(bodylines)
    logging.debug("Bodylines", suffix=body)
    # Cannot use Python gnupg wrapper: Requires GPG 1.x to verify
    # Copy env for gnupg without locale
    env = {}
    for k in os.environ:
        if not k.startswith('LC_'):
            env[k] = os.environ[k]
    env['LANG'] = 'C'
    env['TZ'] = 'UTC'
    res = subprocess.run(['gpg1', '--pgp2', '--verify'],
                         env=env, input=body.encode('ASCII'),
                         stderr=subprocess.PIPE)
    stderr = maybe_decode(res.stderr)
    logging.complete(stderr)
    if res.returncode != 0:
        logging.error("gpg1 return code %d (%r)" % (res.returncode, stderr))
        return False
    if '\ngpg: Good signature' not in stderr:
        logging.error("Missing good signature (%r)" % stderr)
        return False
    if not stderr.startswith('gpg: Signature made '):
        logging.error("No signature made (%r)" % stderr)
        return False
    if not ((' key ID %s\n' % autoblockchainify.config.arg.stamper_keyid)
            in stderr):
        logging.error("Signature by wrong KeyID (%r)" % stderr)
        return False
    try:
        sigtime = datetime.strptime(stderr[24:48], "%b %d %H:%M:%S %Y %Z")
        logging.xdebug("Extracted date %r" % sigtime)
    except ValueError:
        logging.error("Illegal signature date format %r (%r)" %
                      (stderr[24:48], stderr))
        return False
    if sigtime > datetime.utcnow() + timedelta(seconds=30):
        logging.error("Signature time %s lies more than 30 seconds in the future"
                      % sigtime)
        return False
    modtime = datetime.utcfromtimestamp(stat.st_mtime)
    if sigtime < modtime - timedelta(seconds=30):
        logging.error("Signature time %s is more than 30 seconds before "
                      "file modification time %s"
                      % (sigtime, modtime))
        return False
    return True


def verify_body_and_save_signature(body, stat, logfile, msgno):
    bodylines = extract_pgp_body(body)
    if bodylines is None:
        logging.error("No body lines")
        return False

    res = body_contains_file(bodylines, logfile)
    if res is None:
        logging.error("File contents not in message %s" % msgno)
        return False
    else:
        (before, after) = res
        logging.debug("Message wrapped in %d lines before, %d after" %
                      (before, after))
        if before > 20 or after > 20:
            logging.error("Too many lines added by the PGP Timestamping Server"
                          " before (%d)/after (%d) our contents" % (before, after))
            return False

    if not body_signature_correct(bodylines, stat):
        logging.error("Body signature incorrect")
        return False

    save_signature(bodylines, logfile)
    return True


def body_contains_file(bodylines, logfile):
    if bodylines is None:
        return None
    linesbefore = 0
    with logfile.open(mode='r') as f:
        # A few empty/comment lines at the beginning
        firstline = f.readline().rstrip()
        for i in range(len(bodylines)):
            if bodylines[i] == firstline:
                break
            elif bodylines[i] == '' or bodylines[i][0] in '#-':
                linesbefore += 1
            else:
                return None
        # Now should be contiguous
        i += 1
        for line in f:
            if bodylines[i] != line.rstrip():
                return None
            i += 1
        # Now there should only be empty lines and a PGP signature
        linesafter = len(bodylines) - i
        i += 1
        while bodylines[i] == '':
            i += 1
        if bodylines[i] != '-----BEGIN PGP SIGNATURE-----':
            return None
        # No further line starting with '-'
        for i in range(i + 1, len(bodylines) - 1):
            if bodylines[i] != '' and bodylines[i][0] == '-':
                return None
        return (linesbefore, linesafter)


def file_unchanged(stat, logfile):
    try:
        cur_stat = logfile.stat()
        unchanged = (cur_stat.st_mtime == stat.st_mtime
                     and cur_stat.st_ino == stat.st_ino)
        logging.xdebug("%r unchanged: %r" % (logfile, unchanged))
        return unchanged
    except FileNotFoundError:
        logging.xdebug("%r unchanged: missing" % logfile)
        return False


def imap_idle(imap, stat, logfile):
    while True:
        imap.send(b'%s IDLE\r\n' % (imap._new_tag()))
        logging.pause("IMAP idling")
        line = imap.readline().strip()
        logging.debug("IMAP IDLE → %s" % line)
        if line != b'+ idling':
            logging.error("IMAP IDLE unsuccessful")
            return False
        # Wait for new message
        while file_unchanged(stat, logfile):
            line = imap.readline().strip()
            if line == b'' or line.startswith(b'* BYE '):
                return False
            match = re.match(r'^\* ([0-9]+) EXISTS$', str(line, 'ASCII'))
            if match:
                logging.success("You have new mail %s!"
                                % match.group(1).encode('ASCII'))
                # Stop idling
                imap.send(b'DONE\r\n')
                if check_for_stamper_mail(imap, stat, logfile) is True:
                    logging.xdebug("Returning from success after idling")
                    return False
                break  # Restart IDLE command
            # Otherwise: Uninteresting untagged response, continue idling
        logging.stop("Next mail sent, giving up waiting on now-old reply")


def check_for_stamper_mail(imap, stat, logfile):
    # See `--no-dovecot-bug-workaround`:
    query = ('FROM', '"%s"' % autoblockchainify.config.arg.stamper_from,
             'UNSEEN',
             'LARGER', str(stat.st_size),
             'SMALLER', str(stat.st_size + 16384))
    logging.debug("IMAP SEARCH " + (' '.join(query)))
    (typ, msgs) = imap.search(None, *query)
    logging.info("IMAP SEARCH → %s, %s" % (typ, msgs))
    if len(msgs) == 1 and len(msgs[0]) > 0:
        mseq = msgs[0].replace(b' ', b',')
        (typ, contents) = imap.fetch(mseq, 'BODY[TEXT]')
        logging.debug("IMAP FETCH → %s (%d)" % (typ, len(contents)))
        remaining_msgids = mseq.split(b',')
        for m in contents:
            if m != b')':
                msgid = remaining_msgids[0]
                remaining_msgids = remaining_msgids[1:]
                logging.debug("IMAP FETCH BODY (%s) → %s…" %
                              (msgid, m[1][:20]))
                if verify_body_and_save_signature(m[1], stat, logfile, msgid):
                    logging.success(
                        "Successful answer in message %s; deleting" % msgid)
                    imap.store(msgid, '+FLAGS', '\\Deleted')
                    return True
    return False


def wait_for_receive(logfile):
    try:
        logging.start("wait_for_receive", level=signale.XDEBUG,
                      suffix="Threads: " + str(threading.enumerate()))
        with serialize_receive:
            if not logfile.is_file():
                logging.warning("Logfile vanished, should not happen")
                return
            stat = logfile.stat()
            logging.debug("Timestamp revision file is from %d" % stat.st_mtime)
            (host, port) = split_host_port(
                autoblockchainify.config.arg.stamper_imap_server, 143)
            with IMAP4(host=host, port=port) as imap:
                imap.starttls()
                imap.login(autoblockchainify.config.arg.stamper_username,
                           autoblockchainify.config.arg.stamper_password)
                imap.select('INBOX')
                if not check_for_stamper_mail(imap, stat, logfile):
                    # No existing message found, wait for more incoming messages
                    # and process them until definitely okay or giving up for good
                    if 'IDLE' in imap.capabilities:
                        imap_idle(imap, stat, logfile)
                    else:
                        logging.warning(
                            "IMAP server does not support IDLE; polling instead")
                        # Poll every minute, for 10 minutes;
                        # see description for `async_email_timestamp` below.
                        for _ in range(10):
                            time.sleep(60)
                            if check_for_stamper_mail(imap, stat, logfile):
                                logging.success("Polling found matching mail")
                                return
                        logging.stop("No response received, giving up")
        logging.success("Returning from mail thread", level=signale.XDEBUG)
    except Exception:
        logging.exception("Unhandled exception in mail thread")


def modified_in(file, wait):
    """Has `logfile` not been modified in ~`wait` seconds?
    Non-existent file is considered to *not* fulfill this."""
    try:
        stat = file.stat()
        mtime = datetime.utcfromtimestamp(stat.st_mtime)
        now = datetime.utcnow()
        logging.xdebug("modified_in(%s, %s): mtime %s, now %s" %
                       (file, wait, mtime, now))
        return mtime + wait >= now
    except FileNotFoundError:
        logging.xdebug("modified_in: %s not found" % file)
        return False


# * `resume=True`: Run once at startup, to wait for a possibly pending
#   outstanding mail reply, indicated by the presence of the logfile.
#   Cases:
#   1. Pending email (indicated by logfile)
#      - Wait for reply (should already have arrived or in the next 5 minutes)
#      - Abort when new logfile arrives
#   2. No pending mail
#      - Do nothing, wait for next commit
# * `resume=False`: Run at least once every
#   `commit_interval * force_after_intervals` (± some jitter).
#   sigfile may be generated up to about 5 minutes later (mail
#   timestamper processes mails on every full 5-minute interval).
#   Cases:
#   1. First commit (no sigfile yet)
#      - Send mail unconditionally
#      - Wait for reply, abort when new logfile arrives
#   2. Only one forced commit every force interval:
#      - Send mail unconditionally on every commit
#      - Wait for reply, abort when new logfile arrives
#   3. Frequent changes (several of the commit_intervals):
#      - Previous sigfile should already have been committed
#        (as we are called only when a commit has just been made)
#      - Send mail when mail reply would be received no
#        earlier than the previous sigfile date plus force_interval
#      - Wait for reply, abort when new logfile arrives
#   4. Previous mail has not been replied to (mail problem or too frequent)
#      - Force send after force_interval anyway
#      - Wait for reply, abort when new logfile arrives
#   Solution:
#   - Trigger new mail 3…4 minutes before sigfile time+force_interval
#     (assuming that force_interval is a multiple of 5 minutes; if
#     not, mails might be up to 3…4 minutes more frequent than
#     force_interval, possibly causing more than one mail per
#     forced commit, i.e., some work by the PGP timestamper is wasted)
#   - The minimum force_interval has to greater than 4+5 minutes
#   - Do not trigger new mail if logfile exists and has been written to in the
#     past 4+5-epsilon minutes
# Note: `wait` is almost 1 commit_interval shorter than forced_interval
# (see `do_commit()`.)
def needs_timestamp(log=False):
    if not autoblockchainify.config.arg.stamper_own_address:
        if log:
            logging.debug("Timestamping by mail not configured")
        return False
    path = autoblockchainify.config.arg.repository
    logfile = Path(path, 'pgp-timestamp.tmp')
    sigfile = Path(path, 'pgp-timestamp.sig')
    sigfile_interval = (autoblockchainify.config.arg.commit_interval
                        * autoblockchainify.config.arg.force_after_intervals
                        - timedelta(minutes=4))
    if logfile.is_file() and modified_in(logfile, timedelta(minutes=4+5)):
        if log:
            logging.stop("Logfile more recent than 4+5 minutes, skipping")
        return False
    if not sigfile.is_file() or not modified_in(sigfile, sigfile_interval):
        return True
    else:
        if log:
            logging.debug("Sigfile too fresh")
        return False


def async_email_timestamp(resume=False):
    """If called with `resume=True`, tries to resume waiting for the mail"""
    logging.xdebug("async_email_timestamp(%r)" % resume)
    path = autoblockchainify.config.arg.repository
    repo = git.Repository(path)
    if repo.head_is_unborn:
        logging.stop(
            "Cannot timestamp by email yet: repository without commits")
        return
    head = repo.head
    logfile = Path(path, 'pgp-timestamp.tmp')
    if resume:
        if not logfile.is_file():
            logging.stop("Not resuming mail timestamp: No pending mail reply")
            return
        with logfile.open() as f:
            contents = f.read()
        logging.xdebug("Resuming with logfile contents: %r" % contents)
        if len(contents) < 40:
            logging.stop("Not resuming mail timestamp: No revision info")
            return
        threading.Thread(target=wait_for_receive, args=(logfile,), name="mail_resume",
                         daemon=True).start()
    else:  # Fresh request
        # No recent attempts or results for mail timestamping
        if needs_timestamp(log=True):
            new_rev = ("git commit %s\nTimestamp requested at %s\n" %
                       (head.target.hex,
                        strftime("%Y-%m-%d %H:%M:%S UTC", gmtime())))
            logging.xdebug("Creating logfile with: %r" % new_rev)
            with serialize_create:
                with logfile.open('w') as f:
                    f.write(new_rev)
                send(new_rev)
            threading.Thread(target=wait_for_receive, args=(logfile,), name="mail",
                             daemon=True).start()
