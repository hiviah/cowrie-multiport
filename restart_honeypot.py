#!/usr/bin/env python

"""
Restarter script, because that fucking tamagotchi won't quit eating RAM
"""

import sys
import os
import os.path
import time
import logging
import signal
import subprocess

cowrieDir = os.path.dirname(os.path.realpath(__file__))

cowriePidFile = cowrieDir + "/cowrie.pid"
logFile = cowrieDir + "/restart_honeypot.log"
stopScript = cowrieDir + "/stop.sh"
startScript = cowrieDir + "/start.sh"
waitSeconds = 60

def pidAlive(pid):
    """ Check for the existence of a unix pid. """
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True

logging.basicConfig(filename=logFile, level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s [%(pathname)s:%(lineno)d]")

logging.info("Honeyport restarter invoked")

if not os.path.isfile(cowriePidFile):
    logging.info("No pid file, bailing out")
    sys.exit(1)

try:
    with open(cowriePidFile) as pidFile:
        pid = int(pidFile.read().rstrip())
except IOError:
    logging.exception("Couldn't read cowrie pidfile")
    sys.exit(2)

if not pidAlive(pid):
    logging.info("Cowrie process not running, not starting again")
    sys.exit(1)

logging.info("Restarting cowrie process %d, will wait for %d seconds for it to die", pid, waitSeconds)

subprocess.call([stopScript], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

for sec in range(waitSeconds):
    time.sleep(1)
    if not pidAlive(pid):
        logging.info("Cowrie died gracefully after %d seconds", sec)
        break

# we need SIGKILL if graceful shutdown wasn't enough
if pidAlive(pid):
    try:
        logging.warn("PID %d still alive after graceful shutdown, going for SIGKILL", pid)
        os.kill(pid, signal.SIGKILL)
        time.sleep(2)
    except OSError:
        logging.exception("Kill failed, maybe it fizzled")
    if pidAlive(pid):
        logging.warn("PID %d alive after SIGKILL, did it get stuck in kernel?". pid)
        sys.exit(3)

try:
    subprocess.check_output([startScript], stdin=subprocess.PIPE, stderr=subprocess.STDOUT)
    logging.info("Start script called")
except:
    logging.exception("Start script ended with nonzero status")


