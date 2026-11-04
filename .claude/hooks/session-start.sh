#!/bin/bash
set -euo pipefail

# Only run in Claude Code cloud sessions
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}"

# Install ppt-master Python dependencies into the system Python.
# Skip if neither this script nor the requirements file changed since the last successful install.
req=.claude/skills/ppt-master/requirements.txt
pyhashes="$(python3 -I -c 'import sysconfig; print(sysconfig.get_path("purelib"))')/.session-start.sha256"
if ! sha256sum --check --status "$pyhashes" 2>/dev/null; then
  rm -f "$pyhashes"
  # Debian ships blinker without a RECORD file, which blocks flask's upgrade; install over it.
  python3 -m pip install -q --ignore-installed blinker
  python3 -m pip install -q -r "$req"
  sha256sum .claude/hooks/session-start.sh "$req" > "$pyhashes" || rm -f "$pyhashes"
fi
