URL=https://www.geocaching.com/api/proxy/web/search?box=$1%2C$2%2C$3%2C$4
# TODO: Loop with skip as long as there are more results
./oauth_token.py | jq -r .access_token | xargs echo "Authorization: Bearer" | curl --silent $URL -H @- | jq .
