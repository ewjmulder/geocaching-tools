#!/bin/bash
# Script to get all caches in a certain rectangle area
# Usage: get_caches.sh lat-top-left lon-top-left lat-bottom-right lon-bottom-right [skip] [take]

# If skip is not set, default to 0
SKIP=$5
if [ -z "$SKIP" ]
  then
    SKIP=0
fi
# If take is not set, default to 50
TAKE=$6
if [ -z "$TAKE" ]
  then
    TAKE=50
fi

URL=https://www.geocaching.com/api/proxy/web/search?box=$1%2C$2%2C$3%2C$4\&skip=$SKIP\&take=$TAKE
./oauth_token.py | jq -r .access_token | xargs echo "Authorization: Bearer" | curl --silent $URL -H @- | jq .
