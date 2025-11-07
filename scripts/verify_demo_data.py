#!/usr/bin/env python3
"""Weryfikacja danych demonstracyjnych."""

import httpx
import asyncio

API_BASE = "http://localhost:8000/api/v1"
TOKEN = None


async def login():
    """Login i pobranie tokenu."""
    global TOKEN
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{API_BASE}/auth/login",
            json={"email": "demo@sight.pl", "password": "Demo2025!Sight"}
        )
        TOKEN = resp.json()["access_token"]


async def verify():
    """Weryfikacja wszystkich danych."""
    await login()

    headers = {"Authorization": f"Bearer {TOKEN}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Pobierz projekty
        resp = await client.get(f"{API_BASE}/projects", headers=headers)
        projects = resp.json()

        print("=" * 60)
        print("WERYFIKACJA DANYCH DEMONSTRACYJNYCH - SIGHT")
        print("=" * 60)
        print(f"\nŁącznie projektów: {len(projects)}\n")

        total_personas = 0
        total_surveys = 0
        total_fgs = 0

        for p in projects:
            print(f"📁 {p['name']}")
            print(f"   ID: {p['id'][:8]}...")

            # Person
            resp = await client.get(f"{API_BASE}/projects/{p['id']}/personas", headers=headers)
            personas = resp.json()
            print(f"   👥 Person: {len(personas)}")
            total_personas += len(personas)

            # Ankiety
            resp = await client.get(f"{API_BASE}/projects/{p['id']}/surveys", headers=headers)
            surveys = resp.json()
            print(f"   📊 Ankiety: {len(surveys)}")
            total_surveys += len(surveys)

            # Focus Groups
            resp = await client.get(f"{API_BASE}/projects/{p['id']}/focus-groups", headers=headers)
            fgs = resp.json()
            print(f"   💬 Focus Groups: {len(fgs)}")
            total_fgs += len(fgs)
            print()

        print("=" * 60)
        print("PODSUMOWANIE:")
        print("=" * 60)
        print(f"✓ Projekty: {len(projects)}")
        print(f"✓ Persony: {total_personas}")
        print(f"✓ Ankiety: {total_surveys}")
        print(f"✓ Focus Groups: {total_fgs}")
        print()
        print("Wszystkie dane dostępne w UI:")
        print("http://localhost:5173")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(verify())
