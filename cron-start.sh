#!/bin/sh

cd $(dirname $0)
echo "$(date -u)\tStarting cowrie" >> cron-start.log
./start.sh >> cron-start.log 2>&1

