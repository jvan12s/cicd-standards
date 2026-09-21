#!/usr/bin/env bash
# Setzt die Branch-Protection-Regeln aus dem CI/CD-Konzept auf `main` eines
# Projekt-Repos. Erfordert die GitHub CLI (`gh`), eingeloggt mit ausreichend
# Rechten (`gh auth login`).
#
# Nutzung:
#   ./setup-branch-protection.sh <owner>/<repo> [status-check-name ...]
#
# Beispiel:
#   ./setup-branch-protection.sh jrvdm/introduction-website \
#     "Reusable CI (Node) / build-test-lint"

set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "Fehler: GitHub CLI ('gh') ist nicht installiert. Siehe https://cli.github.com/" >&2
  exit 1
fi

if [ "$#" -lt 1 ]; then
  echo "Nutzung: $0 <owner>/<repo> [status-check-name ...]" >&2
  exit 1
fi

REPO="$1"
shift
CHECKS=("$@")

CONTEXTS_JSON="[]"
if [ "${#CHECKS[@]}" -gt 0 ]; then
  CONTEXTS_JSON=$(printf '%s\n' "${CHECKS[@]}" | jq -R . | jq -s .)
fi

echo "Setze Branch Protection für ${REPO}#main ..."

gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  "repos/${REPO}/branches/main/protection" \
  --input - <<EOF
{
  "required_status_checks": {
    "strict": true,
    "contexts": ${CONTEXTS_JSON}
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true
}
EOF

echo "Deaktiviere Auto-Approval von PRs durch Actions ..."
gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  "repos/${REPO}/actions/permissions/workflow" \
  --input - <<'EOF'
{
  "default_workflow_permissions": "read",
  "can_approve_pull_request_reviews": false
}
EOF

echo "Fertig. Bitte in den Repo-Einstellungen unter Code security prüfen:"
echo "  - Secret scanning + Push protection aktivieren"
echo "  - Dependabot alerts + security updates aktivieren"
echo "  - CodeQL Default Setup aktivieren (oder den reusable-security.yml Workflow einbinden)"
