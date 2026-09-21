# cicd-standards

Wiederverwendbare CI/CD-Bausteine für alle Projekte, die über das
Subagent-Team (frontend-dev / backend-dev / general-purpose) entstehen.
Konzept-Hintergrund und Begründung: siehe der Plan, der dieses Repo
hervorgebracht hat (GitHub Flow + risikogestaffelte Review-Gates,
Audit-Trail, DSGVO-Guard, Security-Scans).

## Was hier drin ist

- `.github/workflows/reusable-ci-node.yml` — CI für Node/TypeScript-Projekte
  (frontend-dev-Output: Web, React, Astro, ...)
- `.github/workflows/reusable-ci-python.yml` — CI für Python-Projekte
  (backend-dev-Output: FastAPI, ...)
- `.github/workflows/reusable-security.yml` — CodeQL-Scan
- `.github/dependabot.yml.template` — Dependabot-Vorlage (Actions + npm/pip)
- `CODEOWNERS.template` — Pflicht-Review für sicherheitskritische Pfade
- `scripts/dsgvo_guard.py` — CI-Gate gegen personenbezogene Daten in
  Test-/Fixture-Dateien (E-Mails, IBANs, Telefonnummern), mit Tests unter
  `tests/`
- `scripts/setup-branch-protection.sh` — setzt Branch-Protection-Regeln auf
  `main` eines Projekt-Repos per GitHub CLI

## Ein neues Projekt einbinden

1. **Repo hat `main` als Standardbranch**, kein direkter Push darauf.

2. **CI-Workflow im Projekt anlegen**, z. B. `.github/workflows/ci.yml`:

   ```yaml
   name: CI
   on:
     pull_request:
     push:
       branches: [main]

   jobs:
     ci:
       uses: <DEIN-GITHUB-USER>/cicd-standards/.github/workflows/reusable-ci-node.yml@main
       # für Python-Projekte stattdessen:
       # uses: <DEIN-GITHUB-USER>/cicd-standards/.github/workflows/reusable-ci-python.yml@main
   ```

   Für Security-Scans zusätzlich:

   ```yaml
     security:
       uses: <DEIN-GITHUB-USER>/cicd-standards/.github/workflows/reusable-security.yml@main
       with:
         language: javascript-typescript # oder "python"
       permissions:
         security-events: write
         contents: read
   ```

3. **`CODEOWNERS.template`** nach `CODEOWNERS` im Projekt kopieren,
   `<DEIN-GITHUB-USER>` ersetzen.

4. **`.github/dependabot.yml.template`** nach `.github/dependabot.yml`
   kopieren, nicht benötigte `package-ecosystem`-Blöcke entfernen.

5. **Branch Protection setzen:**

   ```bash
   ./scripts/setup-branch-protection.sh <owner>/<repo> "CI / ci"
   ```

6. In den Repo-Einstellungen (Settings → Code security) aktivieren:
   Secret scanning, Push protection, Dependabot alerts + security updates.

7. Optional, bei Projekten mit Abnahme-/Store-Zyklen (Mobile, Kundendeliverables):
   SemVer-Git-Tags für Releases statt eines vollen GitFlow-Branch-Modells.

## Wichtig nach dem ersten Push dieses Repos

Die Default-Werte `<DEIN-GITHUB-USER>/cicd-standards` und `standards-ref: main`
in den `reusable-ci-*.yml`-Workflows sind Platzhalter. Nach dem ersten Push:

1. `<DEIN-GITHUB-USER>` in allen Vorlagen durch den echten GitHub-Namen ersetzen.
2. Sobald ein erstes stabiles Release getaggt ist (z. B. `v1`), `standards-ref`
   in konsumierenden Projekten auf diesen Tag/SHA pinnen statt auf `main` —
   das schließt die Lücke im Supply-Chain-Hardening (siehe Recherche zu
   SHA-Pinning von Third-Party-Actions, analog hier auf das eigene Repo
   angewendet).

## DSGVO-Guard lokal testen

```bash
python3 scripts/dsgvo_guard.py --root /pfad/zu/projekt
```

Fund ist kein Blocker per se — reservierte Test-Domains (`example.com`,
`*.test`, ...) verwenden, projektspezifische Ausnahmen in
`.dsgvo-guard-allowlist` eintragen, oder Zeile mit `# dsgvo-guard: allow`
markieren.

## Tests dieses Repos

```bash
python3 -m unittest discover tests -v
```
