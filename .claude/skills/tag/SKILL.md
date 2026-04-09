---
description: Set session tags for the current project. Usage: /tag phase:development feature:auth
---

# Set Session Tags

Parse `$ARGUMENTS` as space-separated `key:value` pairs and set the active session context.

Run this Bash command to validate and apply the tags:

```bash
python3 -c "
import re, json, sys, os, urllib.request, datetime

args     = '$ARGUMENTS'
work_dir = os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())

# Load config
try:
    import yaml
    cfg  = yaml.safe_load(open(os.path.join(work_dir, 'aicli.yaml'))) or {}
    sess = cfg.get('session', {}) or {}
    valid_keys   = sess.get('valid_tag_keys', ['phase','feature','bug','task','component','doc_type','design','decision','meeting','customer'])
    backend_url  = cfg.get('backend_url', 'http://localhost:8000').rstrip('/')
    active_proj  = cfg.get('active_project', 'aicli')
    workspace    = cfg.get('workspace_dir', os.path.join(work_dir, 'workspace'))
except Exception:
    valid_keys  = ['phase','feature','bug','task','component','doc_type','design','decision','meeting','customer']
    backend_url = 'http://localhost:8000'
    active_proj = 'aicli'
    workspace   = os.path.join(work_dir, 'workspace')

# Parse key:value pairs
pairs   = re.findall(r'(\w[\w-]*):([\S]+)', args)
valid   = {k: v for k, v in pairs if k in valid_keys}
invalid = [k for k, v in pairs if k not in valid_keys]

if invalid:
    print(f'ERROR: Unknown tag key(s): {invalid}')
    print(f'Valid keys: {valid_keys}')
    sys.exit(1)

if not valid:
    print('ERROR: No valid tags found.')
    print(f'Usage: /tag phase:development feature:my-feature')
    print(f'Valid keys: {valid_keys}')
    sys.exit(1)

# Write .agent-context
ctx_file = os.path.join(workspace, active_proj, '_system', '.agent-context')
os.makedirs(os.path.dirname(ctx_file), exist_ok=True)

existing_count = 0
try:
    existing = json.loads(open(ctx_file).read())
    existing_count = existing.get('prompt_count', 0)
except Exception:
    pass

ctx = {
    'session_src': 'claude_cli',
    'tags': valid,
    'set_at': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
    'prompt_count': existing_count,
}
open(ctx_file, 'w').write(json.dumps(ctx, indent=2))

# POST to backend
body = json.dumps({
    'phase':   valid.get('phase'),
    'feature': valid.get('feature'),
    'bug_ref': valid.get('bug'),
    'extra':   {k: v for k, v in valid.items() if k not in ('phase','feature','bug')},
}).encode()
req = urllib.request.Request(
    backend_url + '/history/session-tags?project=' + active_proj,
    data=body, headers={'Content-Type': 'application/json'}, method='PUT'
)
try:
    urllib.request.urlopen(req, timeout=3)
    backend_ok = True
except Exception:
    backend_ok = False

tags_display = '  '.join(f'{k}:{v}' for k, v in valid.items())
print(f'Tags set: {tags_display}')
if not backend_ok:
    print('(backend offline — saved to .agent-context only)')
"
```

After running the command:
- If it prints `Tags set: ...` → confirm to the user with the displayed tags
- If it prints `ERROR:` → show the error message and valid keys to the user
- Do not add any commentary beyond confirming the result
