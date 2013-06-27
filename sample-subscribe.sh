curl -u "knabar" -i \
  https://api.github.com/hub \
  -F "hub.mode=subscribe" \
  -F "hub.topic=https://github.com/stick/redmine-scm-integration/events/pull_request.json" \
  -F "hub.callback=http://envy.glencoesoftware.com:19090/event"
