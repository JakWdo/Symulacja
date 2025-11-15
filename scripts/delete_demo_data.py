#!/usr/bin/env python3
"""
Skrypt do usuwania wszystkich danych demonstracyjnych dla konta demo@sight.pl.

Usuwa wszystkie projekty wraz z powiązanymi:
- Personami
- Ankietami i odpowiedziami
- Focus groups i dyskusjami
- Analizami

Usage:
    python scripts/delete_demo_data.py --api-base https://sight-193742683473.europe-central2.run.app/api/v1
    python scripts/delete_demo_data.py  # dla lokalnego developmentu
"""

import asyncio
import httpx
import argparse
import sys
from typing import Optional
from datetime import datetime

# Domyślne wartości
DEFAULT_API_BASE_CLOUD = "https://sight-193742683473.europe-central2.run.app/api/v1"
DEFAULT_API_BASE_LOCAL = "http://localhost:8000/api/v1"
DEFAULT_EMAIL = "demo@sight.pl"
DEFAULT_PASSWORD = "Demo2025!Sight"

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


class DemoDataCleaner:
    """Klasa do usuwania danych demo."""

    def __init__(self, api_base: str, email: str, password: str, dry_run: bool = False):
        self.api_base = api_base
        self.email = email
        self.password = password
        self.dry_run = dry_run
        self.token: Optional[str] = None
        self.headers: dict = {"Content-Type": "application/json"}

    async def login(self, client: httpx.AsyncClient) -> bool:
        """Loguje się i pobiera JWT token."""
        print(f"🔐 Logowanie jako {self.email}...")

        for attempt in range(MAX_RETRIES):
            try:
                response = await client.post(
                    f"{self.api_base}/auth/login",
                    json={"email": self.email, "password": self.password},
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    self.token = data['access_token']
                    self.headers["Authorization"] = f"Bearer {self.token}"
                    print(f"✓ Zalogowano pomyślnie")
                    return True
                elif response.status_code == 401:
                    print(f"✗ Błędne dane logowania dla {self.email}")
                    return False
                else:
                    print(f"⚠ Login attempt {attempt + 1} failed: {response.status_code}")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY)
            except Exception as e:
                print(f"⚠ Login attempt {attempt + 1} error: {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY)

        print(f"✗ Nie udało się zalogować po {MAX_RETRIES} próbach")
        return False

    async def get_all_projects(self, client: httpx.AsyncClient) -> list:
        """Pobiera wszystkie projekty użytkownika."""
        try:
            response = await client.get(
                f"{self.api_base}/projects",
                headers=self.headers,
                timeout=30.0
            )

            if response.status_code == 200:
                projects = response.json()
                print(f"📊 Znaleziono {len(projects)} projektów")
                return projects
            else:
                print(f"✗ Błąd pobierania projektów: {response.status_code}")
                return []
        except Exception as e:
            print(f"✗ Błąd pobierania projektów: {e}")
            return []

    async def get_project_stats(self, client: httpx.AsyncClient, project_id: str) -> dict:
        """Pobiera statystyki projektu (liczba person, ankiet, focus groups)."""
        stats = {
            "personas": 0,
            "surveys": 0,
            "focus_groups": 0
        }

        try:
            # Pobierz persony
            response = await client.get(
                f"{self.api_base}/projects/{project_id}/personas",
                headers=self.headers,
                timeout=30.0
            )
            if response.status_code == 200:
                stats["personas"] = len(response.json())

            # Pobierz ankiety
            response = await client.get(
                f"{self.api_base}/projects/{project_id}/surveys",
                headers=self.headers,
                timeout=30.0
            )
            if response.status_code == 200:
                stats["surveys"] = len(response.json())

            # Pobierz focus groups
            response = await client.get(
                f"{self.api_base}/projects/{project_id}/focus-groups",
                headers=self.headers,
                timeout=30.0
            )
            if response.status_code == 200:
                stats["focus_groups"] = len(response.json())

        except Exception as e:
            print(f"  ⚠ Błąd pobierania statystyk: {e}")

        return stats

    async def delete_project(self, client: httpx.AsyncClient, project_id: str, project_name: str) -> bool:
        """Usuwa projekt wraz ze wszystkimi powiązanymi danymi."""
        if self.dry_run:
            print(f"  [DRY RUN] Usunięto by projekt: {project_name}")
            return True

        for attempt in range(MAX_RETRIES):
            try:
                response = await client.delete(
                    f"{self.api_base}/projects/{project_id}",
                    headers=self.headers,
                    timeout=60.0
                )

                if response.status_code in [200, 204]:
                    print(f"  ✓ Usunięto projekt: {project_name}")
                    return True
                elif response.status_code == 404:
                    print(f"  ⚠ Projekt już nie istnieje: {project_name}")
                    return True
                else:
                    print(f"  ⚠ Delete attempt {attempt + 1}: {response.status_code}")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY)
            except Exception as e:
                print(f"  ⚠ Delete error (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY)

        print(f"  ✗ Nie udało się usunąć projektu: {project_name}")
        return False

    async def clean_all_data(self, client: httpx.AsyncClient) -> dict:
        """Usuwa wszystkie dane demo użytkownika."""
        # Pobierz wszystkie projekty
        projects = await self.get_all_projects(client)

        if not projects:
            print("\n✓ Brak projektów do usunięcia")
            return {
                "total_projects": 0,
                "deleted_projects": 0,
                "total_personas": 0,
                "total_surveys": 0,
                "total_focus_groups": 0
            }

        # Zbierz statystyki
        total_stats = {
            "total_projects": len(projects),
            "deleted_projects": 0,
            "total_personas": 0,
            "total_surveys": 0,
            "total_focus_groups": 0
        }

        print(f"\n{'='*70}")
        print("USUWANIE PROJEKTÓW")
        print(f"{'='*70}\n")

        # Usuń każdy projekt
        for i, project in enumerate(projects, 1):
            project_id = project['id']
            project_name = project['name']

            print(f"[{i}/{len(projects)}] {project_name}")

            # Pobierz statystyki przed usunięciem
            stats = await self.get_project_stats(client, project_id)
            total_stats["total_personas"] += stats["personas"]
            total_stats["total_surveys"] += stats["surveys"]
            total_stats["total_focus_groups"] += stats["focus_groups"]

            print(f"  📊 {stats['personas']} person, {stats['surveys']} ankiet, {stats['focus_groups']} focus groups")

            # Usuń projekt
            if await self.delete_project(client, project_id, project_name):
                total_stats["deleted_projects"] += 1

            # Krótka przerwa między usuwaniem
            await asyncio.sleep(0.5)

        return total_stats


async def main():
    """Główna funkcja - usuwa wszystkie dane demo."""
    parser = argparse.ArgumentParser(
        description='Usuwa wszystkie dane demo dla konta demo@sight.pl'
    )
    parser.add_argument(
        '--api-base',
        default=DEFAULT_API_BASE_LOCAL,
        help=f'API base URL (domyślnie: {DEFAULT_API_BASE_LOCAL})'
    )
    parser.add_argument(
        '--cloud',
        action='store_true',
        help=f'Użyj Cloud Run API ({DEFAULT_API_BASE_CLOUD})'
    )
    parser.add_argument(
        '--email',
        default=DEFAULT_EMAIL,
        help=f'Email konta demo (domyślnie: {DEFAULT_EMAIL})'
    )
    parser.add_argument(
        '--password',
        default=DEFAULT_PASSWORD,
        help='Hasło konta demo'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Tryb testowy - nie usuwa danych, tylko pokazuje co by zostało usunięte'
    )
    parser.add_argument(
        '--yes',
        action='store_true',
        help='Pomiń potwierdzenie - użyj ostrożnie!'
    )

    args = parser.parse_args()

    # Użyj Cloud Run API jeśli --cloud
    if args.cloud:
        api_base = DEFAULT_API_BASE_CLOUD
    else:
        api_base = args.api_base

    print("="*70)
    print("USUWANIE DANYCH DEMO - SIGHT")
    print("="*70)
    print(f"API: {api_base}")
    print(f"Konto: {args.email}")
    if args.dry_run:
        print(f"Tryb: DRY RUN (tylko test, bez faktycznego usuwania)")
    else:
        print(f"Tryb: PRODUKCJA (faktyczne usuwanie danych)")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    print()

    # Potwierdzenie (jeśli nie --yes)
    if not args.yes and not args.dry_run:
        print("⚠️  UWAGA! Ta operacja usunie WSZYSTKIE projekty i powiązane dane.")
        print("    Dane zostaną permanentnie usunięte z bazy danych!")
        print()
        confirmation = input("Czy na pewno chcesz kontynuować? Wpisz 'TAK' aby potwierdzić: ")
        if confirmation != "TAK":
            print("\n✗ Operacja anulowana")
            return 0
        print()

    # Utwórz cleaner i zaloguj
    cleaner = DemoDataCleaner(api_base, args.email, args.password, args.dry_run)

    async with httpx.AsyncClient(timeout=300.0) as client:
        # Zaloguj się
        if not await cleaner.login(client):
            print("\n✗ Nie udało się zalogować - kończę")
            return 1

        print()

        # Usuń wszystkie dane
        try:
            stats = await cleaner.clean_all_data(client)
        except Exception as e:
            print(f"\n✗ Błąd podczas usuwania danych: {e}")
            return 1

    # Podsumowanie
    print("\n" + "="*70)
    if args.dry_run:
        print("✓ DRY RUN UKOŃCZONY")
    else:
        print("✓ USUWANIE DANYCH UKOŃCZONE")
    print("="*70)
    print(f"Projekty: {stats['deleted_projects']}/{stats['total_projects']} usuniętych")
    print(f"Łącznie usuniętych zasobów:")
    print(f"  - Persony: {stats['total_personas']}")
    print(f"  - Ankiety: {stats['total_surveys']}")
    print(f"  - Focus Groups: {stats['total_focus_groups']}")
    print("="*70)

    if args.dry_run:
        print("\nTo był tryb DRY RUN - żadne dane nie zostały usunięte.")
        print("Uruchom bez --dry-run aby faktycznie usunąć dane.")

    return 0 if stats['deleted_projects'] == stats['total_projects'] else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
