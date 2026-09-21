# cicd-standards

Wiederverwendbare CI/CD-Bausteine für alle Projekte, die über das
Subagent-Team (frontend-dev / backend-dev / general-purpose) entstehen.

**Wichtig:** Läuft aktuell auf einem **kostenlosen persönlichen GitHub-Account
mit privaten Repos**. Das begrenzt, was technisch *erzwungen* werden kann —
siehe unten "Was auf dem Free-Plan nicht geht". Was hier steht, ist der
tatsächlich nutzbare Umfang, nicht der ursprünglich angedachte volle Umfang.

## Was auf dem Free-Plan nicht geht (privates Repo, kein Team/Pro)

| Baustein | Status | Warum |
|---|---|---|
| Branch Protection (Pflicht-Review, geschützter `main`, CODEOWNERS-Durchsetzung) | ❌ Nicht aktiv | Braucht GitHub Pro (4 $/Monat) für private Repos |
| Secret Scanning + Push Protection | ❌ Nicht aktiv | Braucht GitHub Advanced Security — nur über eine Organisation mit Team-Plan |
| CodeQL Code Scanning | ❌ Nicht aktiv | Gleiche Sperre wie oben |
| Dependabot Alerts + Security Updates | ✅ Aktiv | Kostenlos für alle Repos/Pläne |
| CI (Tests/Lint/Build, DSGVO-Guard) | ✅ Aktiv | Normale GitHub-Actions-Runs, keine Plan-Sperre |

**Konsequenz:** "Kontrolliert" ist auf diesem Plan aktuell **Konvention, keine
technische Durchsetzung**. `main` lässt sich direkt pushen, ein PR lässt sich
ohne Review mergen, CODEOWNERS-Einträge sind nur Dokumentation. CI-Checks
laufen und zeigen grün/rot — der Merge-Klick entscheidet aber weiterhin der
Mensch, nicht GitHub technisch.

**Push-Konvention (verbindlich, auch ohne technische Durchsetzung):** Nie
direkt auf `main` pushen — immer über einen Pull Request. Fehlende Branch
Protection ist kein Freibrief für Direct-Pushes. Gilt für Menschen und für
jeden Subagenten gleichermaßen (siehe `~/.claude/CLAUDE.md`).

Falls das später wichtiger wird: GitHub Pro (4 $/Monat, Einzelaccount)
schaltet Branch Protection frei. Secret-Scanning/CodeQL bräuchten zusätzlich
eine Organisation mit Team-Plan — deutlich größerer Schritt, aktuell bewusst
nicht gegangen. `scripts/setup-branch-protection.sh` liegt für diesen Fall
bereit, ist aber **nicht Teil des aktuellen Standard-Setups**.

## Was hier drin ist

- `.github/workflows/reusable-ci-node.yml` — CI für Node/TypeScript-Projekte
  (frontend-dev-Output: Web, React, Astro, ...)
- `.github/workflows/reusable-ci-python.yml` — CI für Python-Projekte
  (backend-dev-Output: FastAPI, ...)
- `.github/dependabot.yml.template` — Dependabot-Vorlage (Actions + npm/pip)
- `CODEOWNERS.template` — dokumentiert Verantwortlichkeit für sensible Pfade
  (aktuell nur Konvention, siehe oben)
- `scripts/dsgvo_guard.py` — CI-Gate gegen personenbezogene Daten in
  Test-/Fixture-Dateien (E-Mails, IBANs, Telefonnummern), mit Tests unter
  `tests/`
- `scripts/setup-branch-protection.sh` — optional, erst nutzbar mit GitHub
  Pro (private Repos) oder bei öffentlichen Repos

## Ein neues Projekt einbinden

1. **Repo hat `main` als Standardbranch.** Direkter Push ist auf dem
   Free-Plan technisch nicht verhindert — als Konvention trotzdem über PRs
   arbeiten.

2. **CI-Workflow im Projekt anlegen**, z. B. `.github/workflows/ci.yml`:

   ```yaml
   name: CI
   on:
     pull_request:
     push:
       branches: [main]

   jobs:
     ci:
       uses: jvan12s/cicd-standards/.github/workflows/reusable-ci-node.yml@main
       # für Python-Projekte stattdessen:
       # uses: jvan12s/cicd-standards/.github/workflows/reusable-ci-python.yml@main
   ```

3. **`CODEOWNERS.template`** nach `CODEOWNERS` im Projekt kopieren,
   `jvan12s` ersetzen. Dient als Dokumentation, wird ohne GitHub Pro nicht
   technisch erzwungen.

4. **`.github/dependabot.yml.template`** nach `.github/dependabot.yml`
   kopieren, nicht benötigte `package-ecosystem`-Blöcke entfernen. Das ist
   der einzige Security-Baustein, der auf dem Free-Plan tatsächlich aktiv
   greift.

5. Optional, bei Projekten mit Abnahme-/Store-Zyklen (Mobile, Kundendeliverables):
   SemVer-Git-Tags für Releases statt eines vollen GitFlow-Branch-Modells.

## Wichtig nach dem ersten Push dieses Repos

Der Default-Wert `standards-ref: main` in den `reusable-ci-*.yml`-Workflows
ist bewusst so belassen. Sobald ein erstes stabiles Release getaggt ist
(z. B. `v1`), `standards-ref` in konsumierenden Projekten auf diesen Tag/SHA
pinnen statt auf `main` — schließt die Lücke im Supply-Chain-Hardening
(siehe SHA-Pinning der Third-Party-Actions in den Workflows selbst, analog
hier auf das eigene Repo angewendet).

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
