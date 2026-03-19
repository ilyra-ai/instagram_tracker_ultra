import re

with open('templates/dashboard.html', 'r') as f:
    content = f.read()

dashboard_js = re.search(r'<script type="module">.*?</script>', content, re.DOTALL)

# Since we might have lost the original content entirely because we overwrote templates/dashboard.html
# let's just fetch it from git.
