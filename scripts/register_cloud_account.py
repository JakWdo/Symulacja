#!/usr/bin/env python3
"""
Prosty skrypt do rejestracji kont demo w Cloud Run.
"""
import asyncio
import httpx
import json

API_BASE = "https://sight-193742683473.europe-central2.run.app/api/v1"

async def register_account(email: str, password: str, full_name: str):
    """Rejestruje nowe konto."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        data = {
            "email": email,
            "password": password,
            "full_name": full_name
        }

        print(f"Rejestruję konto: {email}")
        print(f"Payload: {json.dumps(data, indent=2)}")

        try:
            response = await client.post(
                f"{API_BASE}/auth/register",
                json=data
            )

            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")

            if response.status_code in [200, 201]:
                result = response.json()
                print(f"✓ Konto utworzone pomyślnie")
                print(f"  User ID: {result.get('user', {}).get('id')}")
                print(f"  Token: {result.get('access_token', 'N/A')[:50]}...")
                return True
            else:
                print(f"✗ Błąd rejestracji: {response.text}")
                return False

        except Exception as e:
            print(f"✗ Exception: {e}")
            return False

async def main():
    print("="*70)
    print("REJESTRACJA KONT DEMO W CLOUD RUN")
    print("="*70)
    print()

    # Konto PL
    success_pl = await register_account(
        email="demo@sight.pl",
        password="Demo2025!Sight",
        full_name="Demo User PL"
    )

    print()
    await asyncio.sleep(2)

    # Konto INT
    success_intl = await register_account(
        email="demo-intl@sight.pl",
        password="Demo2025!Sight",
        full_name="Demo User International"
    )

    print()
    print("="*70)
    if success_pl and success_intl:
        print("✓ Oba konta utworzone pomyślnie!")
    elif success_pl or success_intl:
        print("⚠ Tylko jedno konto zostało utworzone")
    else:
        print("✗ Nie udało się utworzyć kont")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
