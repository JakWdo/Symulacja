#!/usr/bin/env python3
"""Ponowne uruchomienie wszystkich analiz AI."""

import httpx
import asyncio


API_BASE = "http://localhost:8000/api/v1"

ACCOUNTS = [
    {"name": "🇵🇱 KONTO POLSKIE", "email": "demo@sight.pl", "password": "Demo2025!Sight"},
    {"name": "🇺🇸 KONTO MIĘDZYNARODOWE", "email": "demo-intl@sight.pl", "password": "Demo2025!Sight"}
]


async def rerun_account(account: dict):
    """Uruchamia ponownie wszystkie analizy dla konta."""
    print(f"\n{account['name']}")
    print("-" * 70)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Login
        resp = await client.post(
            f"{API_BASE}/auth/login",
            json={"email": account['email'], "password": account['password']}
        )
        token = resp.json()['access_token']
        headers = {"Authorization": f"Bearer {token}"}

        # Pobierz projekty
        resp = await client.get(f"{API_BASE}/projects", headers=headers)
        projects = resp.json()

        for p in projects:
            print(f"  📁 {p['name']}")

            # Ankiety
            resp = await client.get(f"{API_BASE}/projects/{p['id']}/surveys", headers=headers)
            surveys = resp.json()

            for survey in surveys:
                try:
                    await client.post(f"{API_BASE}/surveys/{survey['id']}/run", headers=headers)
                    print(f"    → Uruchomiono ankietę: {survey['title']}")
                except Exception as e:
                    print(f"    ✗ Błąd ankiety {survey['title']}: {e}")

            # Focus Groups
            resp = await client.get(f"{API_BASE}/projects/{p['id']}/focus-groups", headers=headers)
            fgs = resp.json()

            for fg in fgs:
                try:
                    await client.post(f"{API_BASE}/focus-groups/{fg['id']}/run", headers=headers)
                    print(f"    → Uruchomiono focus group: {fg['name']}")
                except Exception as e:
                    print(f"    ✗ Błąd focus group {fg['name']}: {e}")

            print()


async def main():
    """Główna funkcja."""
    print("=" * 70)
    print("PONOWNE URUCHOMIENIE ANALIZ AI")
    print("=" * 70)

    for account in ACCOUNTS:
        await rerun_account(account)

    print("=" * 70)
    print("✓ WSZYSTKIE ANALIZY URUCHOMIONE")
    print("=" * 70)
    print()
    print("⏳ Generowanie trwa w tle (~5-10 minut dla wszystkich)")
    print("📊 Sprawdź wyniki w UI: http://localhost:5173")
    print()


if __name__ == "__main__":
    asyncio.run(main())
