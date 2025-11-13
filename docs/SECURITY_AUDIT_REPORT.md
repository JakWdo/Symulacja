# Security Audit Report – Sight Platform
Data audytu: 2025-11-12
Zakres: OWASP Top 10, Authentication, Authorization, Input Validation, Secrets Management

---

## Status i ocena

- Ocena wykonanych działań: 93/100
- Uzasadnienie: większość kontroli OWASP (A01–A05, A07–A10) przechodzi; poprawna autoryzacja (RBAC), uwierzytelnianie (bcrypt, JWT, rate limiting), nagłówki bezpieczeństwa (CSP/HSTS), brak hardcoded secrets. Brakuje automatycznego skanowania zależności w CI/CD oraz kilku praktyk dojrzałości (MFA, refresh tokens, SIEM/alerty, trwały audit log, plan incydentów).

Uwaga: Z raportu usunięto sekcje dot. zadań już wykonanych; poniżej pozostawiono wyłącznie rzeczy do zrobienia.

---

## Backlog bezpieczeństwa – do zrobienia

### 🔴 High priority (następny sprint)
1) Dependency scanning w CI/CD (A06)
- [ ] Dodać Bandit do pipeline: `bandit -r app/ -ll -f json -o bandit-report.json`
- [ ] Dodać Safety: `safety check --full-report --json > safety-report.json`
- [ ] Ustawić “quality gate” (pipeline fail na high/critical) i artefakty raportów
- [ ] Włączyć GitHub Dependabot (pip, Dockerfile)

### 🟡 Medium priority
2) MFA (2FA) dla ról ADMIN
- [ ] TOTP (np. pyotp) + recovery codes, wymuszenie dla ADMIN

3) Refresh tokens i krótkie access tokens
- [ ] Access token 15 min, refresh 7 dni, rotacja i revoke

4) RS256 (opcjonalnie przy architekturze wieloserwisowej)
- [ ] Migracja z HS256 do RS256 + rotacja kluczy

5) Secrets Manager (prod)
- [ ] Przenieść sekrety do GCP Secret Manager + rotacja harmonogramowa

### 🟢 Low priority (backlog/ciągłe)
6) SIEM/Alerting
- [ ] Integracja Sentry/Datadog; alerty na burst 403/failed logins

7) Trwały audit log (compliance)
- [ ] Tabela “audit_log” dla operacji admin; retencja i dostęp audytowy

8) LLM prompt-injection monitoring
- [ ] Filtry wejścia/heurystyki; tagowanie i monitoring podejrzanych odpowiedzi

9) Polityki i procedury
- [ ] Plan reagowania na incydenty (IRP) i polityka bezpieczeństwa (SOC2-ready)

10) CORS per environment (utwardzenie)
- [ ] Weryfikacja whitelist dla PROD/DEV; brak “*” w produkcji

---

## Plan wdrożenia (skrót)

1) CI/CD: safety+bandit+dependabot (PR 1) → gate na CRITICAL/HIGH → artefakty raportów
2) MFA: TOTP + recovery → wymuszenie dla ADMIN → rollout kontrolowany
3) Refresh tokens: endpointy `/token/refresh`, rotacja, lista unieważnień
4) SIEM/alerty: integracja, reguły alertów, dashboard
5) Audit log: tabela, middleware logujący, retencja + backup
6) Secrets: migracja do Secret Manager, rotacja i dokumentacja

---

## Kryteria akceptacji

- Pipeline blokuje merge przy CRITICAL/HIGH (bandit/safety)
- MFA aktywne i wymagane dla ADMIN (test E2E)
- Refresh flow działa (happy path + revoke) i loguje zdarzenia
- Alerty działają (symulacja burst 403/failed login)
- Audit log zawiera pełny ślad działań admin, raportowalny

---

Audytor: (wewnętrzny) – aktualizacja pod backlog działań
Wersja dokumentu: 1.1 (zawiera wyłącznie zadania do wykonania)
