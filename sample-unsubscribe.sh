USER=knabar
REPO=stick/redmine-scm-integration
CALLBACK=http://envy.glencoesoftware.com:19090/event

curl -u $USER -i \
  https://api.github.com/hub \
  -F "hub.mode=unsubscribe" \
  -F "hub.topic=https://github.com/$REPO/events/pull_request.json" \
  -F "hub.callback=$CALLBACK"
