#!/usr/bin/env python3
"""
Script do usuwania danych demonstracyjnych dla platformy Sight w Cloud Run.

Usuwa wszystkie projekty, persony, ankiety, focus groups, environments i teams
dla kont demo (demo-pl@sight.pl i demo-intl@sight.pl).

UWAGA: Ten skrypt usuwa WSZYSTKIE dane z kont demo. Użyj ostrożnie!
"""

import asyncio
import httpx
import argparse
import sys
from typing import Dict, List, Optional
from datetime import datetime

# Domyślne wartości
DEFAULT_API_BASE = "https://sight-193742683473.europe-central2.run.app/api/v1"

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# Account configurations (same as in create_demo_data_cloud.py)
ACCOUNT_CONFIGS = {
    'pl': {
        'email': 'demo-pl@sight.pl',
        'password': 'DemoPL2025!Sight',
        'full_name': 'Demo Użytkownik (Polski)',
        'preferred_language': 'pl',
        'description': 'Konto demonstracyjne z polskimi projektami badawczymi'
    },
    'intl': {
        'email': 'demo-intl@sight.pl',
        'password': 'DemoINTL2025!Sight',
        'full_name': 'Demo User (International)',
        'preferred_language': 'en',
        'description': 'Demo account with international research projects'
    }
}


class CloudDemoDeleter:
    """Klasa do usuwania danych demo w Cloud Run."""

    def __init__(self, api_base: str, email: str, password: str):
        self.api_base = api_base
        self.email = email
        self.password = password
        self.token: Optional[str] = None
        self.headers: Dict[str, str] = {"Content-Type": "application/json"}

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
                    print(f"✗ Błędne dane logowania dla {self.email} lub konto nie istnieje")
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

    async def delete_all_projects(self, client: httpx.AsyncClient) -> int:
        """Usuwa wszystkie projekty użytkownika."""
        print(f"🗑️  Usuwanie projektów...")

        try:
            # Pobierz wszystkie projekty
            response = await client.get(
                f"{self.api_base}/projects",
                headers=self.headers,
                timeout=30.0
            )

            if response.status_code != 200:
                print(f"  ⚠ Nie udało się pobrać projektów: {response.status_code}")
                return 0

            projects = response.json()
            deleted_count = 0

            for project in projects:
                project_id = project['id']
                project_name = project['name']

                for attempt in range(MAX_RETRIES):
                    try:
                        del_response = await client.delete(
                            f"{self.api_base}/projects/{project_id}",
                            headers=self.headers,
                            timeout=30.0
                        )

                        if del_response.status_code in [200, 204]:
                            print(f"  ✓ Usunięto projekt: {project_name}")
                            deleted_count += 1
                            break
                        else:
                            print(f"  ⚠ Delete attempt {attempt + 1} for '{project_name}': {del_response.status_code}")
                            if attempt < MAX_RETRIES - 1:
                                await asyncio.sleep(RETRY_DELAY)
                    except Exception as e:
                        print(f"  ⚠ Delete error (attempt {attempt + 1}) for '{project_name}': {e}")
                        if attempt < MAX_RETRIES - 1:
                            await asyncio.sleep(RETRY_DELAY)

            print(f"  → Usunięto {deleted_count}/{len(projects)} projektów")
            return deleted_count

        except Exception as e:
            print(f"  ✗ Błąd pobierania projektów: {e}")
            return 0

    async def delete_all_environments(self, client: httpx.AsyncClient) -> int:
        """Usuwa wszystkie environments użytkownika."""
        print(f"🗑️  Usuwanie environments...")

        try:
            # Pobierz wszystkie environments
            response = await client.get(
                f"{self.api_base}/environments",
                headers=self.headers,
                timeout=30.0
            )

            if response.status_code != 200:
                print(f"  ⚠ Nie udało się pobrać environments: {response.status_code}")
                return 0

            environments = response.json()
            deleted_count = 0

            for env in environments:
                env_id = env['id']
                env_name = env['name']

                for attempt in range(MAX_RETRIES):
                    try:
                        del_response = await client.delete(
                            f"{self.api_base}/environments/{env_id}",
                            headers=self.headers,
                            timeout=30.0
                        )

                        if del_response.status_code in [200, 204]:
                            print(f"  ✓ Usunięto environment: {env_name}")
                            deleted_count += 1
                            break
                        else:
                            print(f"  ⚠ Delete attempt {attempt + 1} for '{env_name}': {del_response.status_code}")
                            if attempt < MAX_RETRIES - 1:
                                await asyncio.sleep(RETRY_DELAY)
                    except Exception as e:
                        print(f"  ⚠ Delete error (attempt {attempt + 1}) for '{env_name}': {e}")
                        if attempt < MAX_RETRIES - 1:
                            await asyncio.sleep(RETRY_DELAY)

            print(f"  → Usunięto {deleted_count}/{len(environments)} environments")
            return deleted_count

        except Exception as e:
            print(f"  ⚠ Błąd pobierania environments: {e}")
            return 0

    async def delete_all_teams(self, client: httpx.AsyncClient) -> int:
        """Usuwa wszystkie teams użytkownika (oprócz domyślnego)."""
        print(f"🗑️  Usuwanie teams...")

        try:
            # Pobierz wszystkie teams
            response = await client.get(
                f"{self.api_base}/teams/my",
                headers=self.headers,
                timeout=30.0
            )

            if response.status_code != 200:
                print(f"  ⚠ Nie udało się pobrać teams: {response.status_code}")
                return 0

            data = response.json()
            teams = data.get('teams', [])
            deleted_count = 0

            for team in teams:
                team_id = team['id']
                team_name = team['name']

                # Skip default team (user musi mieć przynajmniej jeden team)
                # Można usunąć jeśli API to obsługuje, ale lepiej zostawić
                if team_name == "Demo Team":
                    print(f"  → Pominięto domyślny team: {team_name}")
                    continue

                for attempt in range(MAX_RETRIES):
                    try:
                        del_response = await client.delete(
                            f"{self.api_base}/teams/{team_id}",
                            headers=self.headers,
                            timeout=30.0
                        )

                        if del_response.status_code in [200, 204]:
                            print(f"  ✓ Usunięto team: {team_name}")
                            deleted_count += 1
                            break
                        else:
                            print(f"  ⚠ Delete attempt {attempt + 1} for '{team_name}': {del_response.status_code}")
                            if attempt < MAX_RETRIES - 1:
                                await asyncio.sleep(RETRY_DELAY)
                    except Exception as e:
                        print(f"  ⚠ Delete error (attempt {attempt + 1}) for '{team_name}': {e}")
                        if attempt < MAX_RETRIES - 1:
                            await asyncio.sleep(RETRY_DELAY)

            print(f"  → Usunięto {deleted_count}/{len(teams)} teams")
            return deleted_count

        except Exception as e:
            print(f"  ⚠ Błąd pobierania teams: {e}")
            return 0

    async def delete_all_data(self, client: httpx.AsyncClient) -> Dict[str, int]:
        """
        Usuwa wszystkie dane użytkownika.

        Kolejność jest ważna:
        1. Projekty (zawierają persony, surveys, focus groups)
        2. Environments
        3. Teams (opcjonalnie)

        Returns:
            Dict z liczbą usuniętych elementów per kategoria
        """
        results = {
            'projects': 0,
            'environments': 0,
            'teams': 0
        }

        # 1. Usuń projekty (najpierw, żeby usunąć wszystkie powiązane dane)
        results['projects'] = await self.delete_all_projects(client)
        await asyncio.sleep(2)

        # 2. Usuń environments
        results['environments'] = await self.delete_all_environments(client)
        await asyncio.sleep(2)

        # 3. Usuń teams (opcjonalnie - pomija domyślny team)
        results['teams'] = await self.delete_all_teams(client)

        return results


async def main():
    """Główna funkcja - usuwa dane demo z Cloud Run."""
    parser = argparse.ArgumentParser(
        description='Usuwa dane demo z Cloud Run dla Sight',
        epilog='UWAGA: Ten skrypt usuwa WSZYSTKIE dane z kont demo!'
    )
    parser.add_argument('--api-base', default=DEFAULT_API_BASE, help='Cloud Run API base URL')
    parser.add_argument('--account-type', choices=['pl', 'intl', 'both'], default='both',
                       help='Typ konta: pl (polskie), intl (międzynarodowe), both (oba)')
    parser.add_argument('--confirm', action='store_true',
                       help='Potwierdź usunięcie bez pytania (użyj ostrożnie!)')

    args = parser.parse_args()

    print("="*70)
    print("USUWANIE DANYCH DEMO W CLOUD RUN - SIGHT")
    print("="*70)
    print(f"API: {args.api_base}")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Tryb: {args.account_type}")
    print("="*70)
    print()

    # Determine which accounts to delete
    accounts_to_delete = []
    if args.account_type in ['pl', 'both']:
        accounts_to_delete.append('pl')
    if args.account_type in ['intl', 'both']:
        accounts_to_delete.append('intl')

    print("⚠️  OSTRZEŻENIE: Ten skrypt usunie WSZYSTKIE dane z następujących kont:")
    for account_type in accounts_to_delete:
        config = ACCOUNT_CONFIGS[account_type]
        print(f"  - {config['email']}")
    print()

    # Confirmation prompt (unless --confirm flag is used)
    if not args.confirm:
        response = input("Czy na pewno chcesz kontynuować? (wpisz 'TAK' aby potwierdzić): ")
        if response != 'TAK':
            print("\n✗ Anulowano przez użytkownika")
            return 0

    print("\n🗑️  Rozpoczynam usuwanie danych...\n")

    account_results = {}

    async with httpx.AsyncClient(timeout=300.0) as client:
        for account_type in accounts_to_delete:
            config = ACCOUNT_CONFIGS[account_type]

            print(f"\n{'='*70}")
            print(f"KONTO: {config['email']}")
            print(f"{'='*70}\n")

            # Create deleter for this account
            deleter = CloudDemoDeleter(args.api_base, config['email'], config['password'])

            # Login
            if not await deleter.login(client):
                print(f"\n✗ Nie udało się zalogować do {config['email']} - pomijam")
                account_results[config['email']] = {
                    'error': 'Login failed',
                    'deleted': {}
                }
                continue

            print()

            # Delete all data
            deleted = await deleter.delete_all_data(client)

            account_results[config['email']] = {
                'error': None,
                'deleted': deleted
            }

            print(f"\n{'='*70}")
            print(f"✓ UKOŃCZONO USUWANIE: {config['email']}")
            print(f"{'='*70}")
            print(f"  Projekty: {deleted['projects']}")
            print(f"  Environments: {deleted['environments']}")
            print(f"  Teams: {deleted['teams']}")
            print()

    # Final summary
    print("\n" + "="*70)
    print(f"✓ PODSUMOWANIE FINALNE")
    print("="*70)
    print()
    print("Wyniki per konto:")
    for email, result in account_results.items():
        if result['error']:
            print(f"  ✗ {email}: {result['error']}")
        else:
            deleted = result['deleted']
            print(f"  ✓ {email}:")
            print(f"      Projekty: {deleted['projects']}")
            print(f"      Environments: {deleted['environments']}")
            print(f"      Teams: {deleted['teams']}")
    print("="*70)

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
