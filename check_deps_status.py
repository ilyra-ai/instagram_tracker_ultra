import importlib
import sys

dependencies = [
    'flask', 'sqlalchemy', 'socketio', 'requests', 'bs4', 
    'curl_cffi', 'nodriver', 'cv2', 'ultralytics', 'vaderSentiment',
    'networkx', 'tenacity', 'rich', 'sentry_sdk', 'prometheus_client',
    'stem'
]

missing = []
for dep in dependencies:
    try:
        importlib.import_module(dep)
    except ImportError:
        missing.append(dep)

with open('missing_deps.txt', 'w') as f:
    if missing:
        f.write('\n'.join(missing))
    else:
        f.write('NONE')
