#!/bin/sh

# gathermate-grabber.sh "http://.../all.xml" "days=2" "id:password"

URL=$1
QUERY=$2
USER=$3

curl "$URL" --user $USER -G --data-urlencode $QUERY --connect-timeout 240
