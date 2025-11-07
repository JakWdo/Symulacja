#!/usr/bin/env python3
"""Finalna weryfikacja danych demo na obu kontach."""

import httpx
import asyncio


API_BASE = "http://localhost:8000/api/v1"

ACCOUNTS = [
    {"name": "🇵🇱 KONTO POLSKIE", "email": "demo@sight.pl", "password": "Demo2025!Sight"},
    {"name": "🇺🇸 KONTO MIĘDZYNARODOWE", "email": "demo-intl@sight.pl", "password": "Demo2025!Sight"}
]


async def verify_account(account: dict):
    """Weryfikuje dane dla jednego konta."""
    print(f"\n{account['name']}")
    print("=" * 70)
    print(f"Email: {account['email']}")
    print()

    # Login
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{API_BASE}/auth/login",
            json={"email": account['email'], "password": account['password']}
        )
        token = resp.json()['access_token']
        headers = {"Authorization": f"Bearer {token}"}

        # Projekty
        resp = await client.get(f"{API_BASE}/projects", headers=headers)
        projects = resp.json()

        print(f"PROJEKTY: {len(projects)}")
        print()

        total_personas = 0
        total_surveys = 0
        total_survey_responses = 0
        total_fgs = 0
        total_fg_messages = 0

        for p in projects:
            print(f"  📁 {p['name']}")

            # Person
            resp = await client.get(f"{API_BASE}/projects/{p['id']}/personas", headers=headers)
            personas = resp.json()
            print(f"     👥 Person: {len(personas)}")
            total_personas += len(personas)

            # Ankiety
            resp = await client.get(f"{API_BASE}/projects/{p['id']}/surveys", headers=headers)
            surveys = resp.json()
            print(f"     📊 Ankiety: {len(surveys)}")
            total_surveys += len(surveys)

            for survey in surveys:
                # Sprawdź czy są wyniki
                try:
                    resp = await client.get(f"{API_BASE}/surveys/{survey['id']}/results", headers=headers)
                    if resp.status_code == 200:
                        results = resp.json()
                        responses = results.get('total_responses', 0)
                        total_survey_responses += responses
                        print(f"        - {survey['title']}: {responses} odpowiedzi")
                except:
                    print(f"        - {survey['title']}: ⏳ generowanie...")

            # Focus Groups
            resp = await client.get(f"{API_BASE}/projects/{p['id']}/focus-groups", headers=headers)
            fgs = resp.json()
            print(f"     💬 Focus Groups: {len(fgs)}")
            total_fgs += len(fgs)

            for fg in fgs:
                # Sprawdź status
                try:
                    resp = await client.get(f"{API_BASE}/focus-groups/{fg['id']}", headers=headers)
                    if resp.status_code == 200:
                        fg_data = resp.json()
                        status = fg_data.get('status', 'pending')
                        if status == 'completed':
                            messages = len(fg_data.get('discussion_log', []))
                            total_fg_messages += messages
                            print(f"        - {fg['name']}: ✓ ukończono ({messages} wiadomości)")
                        else:
                            print(f"        - {fg['name']}: ⏳ {status}")
                except:
                    print(f"        - {fg['name']}: ⏳ generowanie...")

            print()

        print("-" * 70)
        print("PODSUMOWANIE:")
        print(f"  Persony:            {total_personas}")
        print(f"  Ankiety:            {total_surveys}")
        print(f"  Odpowiedzi ankiet:  {total_survey_responses}")
        print(f"  Focus Groups:       {total_fgs}")
        print(f"  Wiadomości FG:      {total_fg_messages}")
        print("=" * 70)


async def main():
    """Główna funkcja."""
    print("\n" + "=" * 70)
    print("FINALNA WERYFIKACJA DANYCH DEMONSTRACYJNYCH")
    print("=" * 70)

    for account in ACCOUNTS:
        try:
            await verify_account(account)
        except Exception as e:
            print(f"✗ Błąd przy weryfikacji {account['name']}: {e}")
            continue

    print("\n" + "=" * 70)
    print("✓ WERYFIKACJA UKOŃCZONA")
    print("=" * 70)
    print()
    print("Dostęp do platformy:")
    print("  Frontend: http://localhost:5173")
    print("  API Docs: http://localhost:8000/docs")
    print()
    print("Konta demo:")
    for acc in ACCOUNTS:
        print(f"  {acc['name']}: {acc['email']} / {acc['password']}")
    print()
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
