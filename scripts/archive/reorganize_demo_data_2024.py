#!/usr/bin/env python3
"""
Script do reorganizacji danych demo:
1. Tworzy nowe konto dla projektów międzynarodowych
2. Usuwa projekty INT z konta polskiego
3. Tworzy projekty INT na nowym koncie
4. Uruchamia wszystkie analizy AI
"""

import asyncio
import httpx
from typing import Dict

API_BASE = "http://localhost:8000/api/v1"

# Definicje projektów
INTL_PROJECTS = [
    {
        "name": "Mental Health Awareness Campaign (US)",
        "description": "Understanding barriers and stigma around mental health in American workplaces. Goal: Develop recommendations for corporate mental health programs.",
        "target_audience": "Professionals aged 25-45 in US urban areas, various industries",
        "research_objectives": "1) Identify mental health stigma in workplace, 2) Understand support-seeking barriers, 3) Explore preferred communication channels, 4) Design effective awareness campaigns",
        "target_sample_size": 12,
        "target_demographics": {
            "age": {"25-34": 0.55, "35-44": 0.45},
            "gender": {"male": 0.45, "female": 0.50, "non-binary": 0.05},
            "location": {"New York": 0.25, "Los Angeles": 0.20, "Chicago": 0.18, "San Francisco": 0.20, "Austin": 0.17}
        },
        "num_personas": 12,
        "surveys": [
            {
                "title": "Mental Health in the Workplace Survey",
                "description": "Survey about mental health attitudes, experiences, and workplace support",
                "questions": [
                    {
                        "id": "q1",
                        "type": "single-choice",
                        "title": "How comfortable are you discussing mental health at work?",
                        "options": ["Very comfortable", "Somewhat comfortable", "Neutral", "Somewhat uncomfortable", "Very uncomfortable"],
                        "required": True
                    },
                    {
                        "id": "q2",
                        "type": "multiple-choice",
                        "title": "What prevents you from seeking mental health support?",
                        "options": ["Stigma", "Cost", "Time", "Don't know where to start", "Fear of career impact", "None"],
                        "required": True
                    },
                    {
                        "id": "q3",
                        "type": "rating-scale",
                        "title": "Rate your company's mental health support (1-10)",
                        "scaleMin": 1,
                        "scaleMax": 10,
                        "required": True
                    },
                    {
                        "id": "q4",
                        "type": "open-text",
                        "title": "What would make you more likely to seek mental health support?",
                        "required": False
                    }
                ],
                "target_responses": 500
            }
        ],
        "focus_groups": [
            {
                "name": "Building Supportive Workplace Culture",
                "description": "Discussion about creating mentally healthy work environments",
                "questions": [
                    "What does a mentally healthy workplace look like to you?",
                    "How can leadership reduce mental health stigma?",
                    "What specific programs or benefits would you value most?"
                ],
                "mode": "normal"
            }
        ]
    },
    {
        "name": "Community Safety & Trust Program",
        "description": "Building trust between local communities and government through safety initiatives. Goal: Design community engagement strategies.",
        "target_audience": "US residents aged 30-60, diverse demographics, urban communities",
        "research_objectives": "1) Measure trust in local authorities, 2) Identify safety concerns, 3) Explore community engagement preferences, 4) Recommend trust-building initiatives",
        "target_sample_size": 12,
        "target_demographics": {
            "age": {"30-39": 0.35, "40-49": 0.35, "50-60": 0.30},
            "gender": {"male": 0.48, "female": 0.52},
            "location": {"New York": 0.20, "Chicago": 0.20, "Houston": 0.20, "Philadelphia": 0.20, "Phoenix": 0.20}
        },
        "num_personas": 12,
        "surveys": [
            {
                "title": "Trust in Local Governance Survey",
                "description": "Survey about community safety, trust, and local government engagement",
                "questions": [
                    {
                        "id": "q1",
                        "type": "rating-scale",
                        "title": "How safe do you feel in your neighborhood? (1-10)",
                        "scaleMin": 1,
                        "scaleMax": 10,
                        "required": True
                    },
                    {
                        "id": "q2",
                        "type": "rating-scale",
                        "title": "How much do you trust local authorities? (1-10)",
                        "scaleMin": 1,
                        "scaleMax": 10,
                        "required": True
                    },
                    {
                        "id": "q3",
                        "type": "multiple-choice",
                        "title": "What safety issues concern you most?",
                        "options": ["Crime", "Traffic safety", "Public health", "Environmental hazards", "Emergency preparedness"],
                        "required": True
                    },
                    {
                        "id": "q4",
                        "type": "open-text",
                        "title": "What would increase your trust in local authorities?",
                        "required": False
                    }
                ],
                "target_responses": 500
            }
        ],
        "focus_groups": [
            {
                "name": "Building Community Trust Discussion",
                "description": "Exploring ways to strengthen community-government relationships",
                "questions": [
                    "What makes you trust (or distrust) local authorities?",
                    "How can local government better engage with community?",
                    "What specific safety programs would you support?"
                ],
                "mode": "normal"
            }
        ]
    }
]


async def create_intl_user() -> str:
    """Tworzy nowe konto dla projektów międzynarodowych."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{API_BASE}/auth/register",
            json={
                "email": "demo-intl@sight.pl",
                "password": "Demo2025!Sight",
                "full_name": "Demo International User"
            }
        )
        result = response.json()
        print(f"✓ Utworzono konto międzynarodowe: demo-intl@sight.pl")
        return result['access_token']


async def delete_project(token: str, project_id: str, project_name: str):
    """Usuwa projekt."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        await client.delete(
            f"{API_BASE}/projects/{project_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"  ✓ Usunięto: {project_name}")


async def get_polish_token() -> str:
    """Loguje się na konto polskie."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{API_BASE}/auth/login",
            json={"email": "demo@sight.pl", "password": "Demo2025!Sight"}
        )
        return response.json()['access_token']


async def create_complete_project(client: httpx.AsyncClient, token: str, project_def: Dict) -> Dict:
    """Tworzy kompletny projekt."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # 1. Utwórz projekt
    project_data = {
        "name": project_def['name'],
        "description": project_def['description'],
        "target_audience": project_def['target_audience'],
        "research_objectives": project_def['research_objectives'],
        "target_sample_size": project_def['target_sample_size'],
        "target_demographics": project_def['target_demographics']
    }
    response = await client.post(f"{API_BASE}/projects", json=project_data, headers=headers)
    project = response.json()
    project_id = project['id']
    print(f"  ✓ Projekt: {project['name']}")

    # 2. Generuj persony
    await client.post(
        f"{API_BASE}/projects/{project_id}/personas/generate",
        json={"num_personas": project_def['num_personas'], "adversarial_mode": False, "use_rag": False},
        headers=headers
    )
    print(f"    → Generowanie {project_def['num_personas']} person...")

    # Czekaj na persony
    for i in range(90):
        await asyncio.sleep(1)
        resp = await client.get(f"{API_BASE}/projects/{project_id}/personas", headers=headers)
        personas = resp.json()
        if len(personas) >= project_def['num_personas']:
            print(f"    ✓ Wygenerowano {len(personas)} person")
            break
        if i % 10 == 0 and i > 0:
            print(f"      ... {len(personas)}/{project_def['num_personas']} (czas: {i}s)")

    # Pobierz IDs person
    resp = await client.get(f"{API_BASE}/projects/{project_id}/personas", headers=headers)
    personas = resp.json()
    persona_ids = [p['id'] for p in personas]

    # 3. Utwórz ankiety
    survey_ids = []
    for survey_def in project_def.get('surveys', []):
        resp = await client.post(f"{API_BASE}/projects/{project_id}/surveys", json=survey_def, headers=headers)
        survey = resp.json()
        survey_ids.append(survey['id'])
        print(f"    ✓ Ankieta: {survey['title']}")

    # 4. Utwórz focus groups
    fg_ids = []
    for fg_def in project_def.get('focus_groups', []):
        fg_data = fg_def.copy()
        fg_data['persona_ids'] = persona_ids[:min(len(persona_ids), 10)]
        resp = await client.post(f"{API_BASE}/projects/{project_id}/focus-groups", json=fg_data, headers=headers)
        fg = resp.json()
        fg_ids.append(fg['id'])
        print(f"    ✓ Focus Group: {fg['name']}")

    return {
        'project_id': project_id,
        'survey_ids': survey_ids,
        'focus_group_ids': fg_ids
    }


async def run_survey(client: httpx.AsyncClient, token: str, survey_id: str):
    """Uruchamia zbieranie odpowiedzi ankiety."""
    headers = {"Authorization": f"Bearer {token}"}
    await client.post(f"{API_BASE}/surveys/{survey_id}/run", headers=headers)


async def run_focus_group(client: httpx.AsyncClient, token: str, fg_id: str):
    """Uruchamia symulację focus group."""
    headers = {"Authorization": f"Bearer {token}"}
    await client.post(f"{API_BASE}/focus-groups/{fg_id}/run", headers=headers)


async def main():
    """Główna funkcja."""
    print("=" * 70)
    print("REORGANIZACJA DANYCH DEMO - PODZIAŁ KONT PL/INT")
    print("=" * 70)
    print()

    # 1. Utwórz nowe konto międzynarodowe
    print("KROK 1: Tworzenie konta międzynarodowego")
    print("-" * 70)
    try:
        intl_token = await create_intl_user()
    except Exception:
        # Konto może już istnieć
        print("  ⚠ Konto może już istnieć, loguję się...")
        intl_token = await get_polish_token()  # Temporary, will fix
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_BASE}/auth/login",
                json={"email": "demo-intl@sight.pl", "password": "Demo2025!Sight"}
            )
            intl_token = response.json()['access_token']
            print("  ✓ Zalogowano na konto demo-intl@sight.pl")
    print()

    # 2. Usuń projekty angielskie z konta polskiego
    print("KROK 2: Usuwanie projektów INT z konta polskiego")
    print("-" * 70)
    polish_token = await get_polish_token()

    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {"Authorization": f"Bearer {polish_token}"}
        resp = await client.get(f"{API_BASE}/projects", headers=headers)
        projects = resp.json()

        intl_project_names = ["Mental Health Awareness Campaign (US)", "Community Safety & Trust Program"]
        for project in projects:
            if project['name'] in intl_project_names:
                await delete_project(polish_token, project['id'], project['name'])
    print()

    # 3. Utwórz projekty INT na nowym koncie
    print("KROK 3: Tworzenie projektów INT na koncie międzynarodowym")
    print("-" * 70)
    intl_project_ids = {}

    async with httpx.AsyncClient(timeout=300.0) as client:
        for project_def in INTL_PROJECTS:
            print(f"\n📁 {project_def['name']}")
            result = await create_complete_project(client, intl_token, project_def)
            intl_project_ids[project_def['name']] = result
            await asyncio.sleep(3)
    print()

    # 4. Uruchom wszystkie analizy - KONTO POLSKIE
    print("KROK 4: Uruchamianie analiz AI - KONTO POLSKIE")
    print("-" * 70)

    async with httpx.AsyncClient(timeout=60.0) as client:
        headers_pl = {"Authorization": f"Bearer {polish_token}"}
        resp = await client.get(f"{API_BASE}/projects", headers=headers_pl)
        pl_projects = resp.json()

        for project in pl_projects:
            print(f"\n  📁 {project['name']}")

            # Ankiety
            resp = await client.get(f"{API_BASE}/projects/{project['id']}/surveys", headers=headers_pl)
            surveys = resp.json()
            for survey in surveys:
                await run_survey(client, polish_token, survey['id'])
                print(f"    → Uruchomiono ankietę: {survey['title']}")

            # Focus Groups
            resp = await client.get(f"{API_BASE}/projects/{project['id']}/focus-groups", headers=headers_pl)
            fgs = resp.json()
            for fg in fgs:
                await run_focus_group(client, polish_token, fg['id'])
                print(f"    → Uruchomiono focus group: {fg['name']}")
    print()

    # 5. Uruchom wszystkie analizy - KONTO MIĘDZYNARODOWE
    print("KROK 5: Uruchamianie analiz AI - KONTO MIĘDZYNARODOWE")
    print("-" * 70)

    async with httpx.AsyncClient(timeout=60.0) as client:
        for project_name, ids in intl_project_ids.items():
            print(f"\n  📁 {project_name}")

            # Ankiety
            for survey_id in ids['survey_ids']:
                await run_survey(client, intl_token, survey_id)
                print(f"    → Uruchomiono ankietę")

            # Focus Groups
            for fg_id in ids['focus_group_ids']:
                await run_focus_group(client, intl_token, fg_id)
                print(f"    → Uruchomiono focus group")
    print()

    # 6. Podsumowanie
    print("=" * 70)
    print("✓ REORGANIZACJA UKOŃCZONA!")
    print("=" * 70)
    print()
    print("KONTA DEMO:")
    print(f"  🇵🇱 Polskie:        demo@sight.pl / Demo2025!Sight")
    print(f"  🇺🇸 Międzynarodowe: demo-intl@sight.pl / Demo2025!Sight")
    print()
    print("ANALIZY AI:")
    print("  ⏳ Ankiety i focus groups generują się w tle (~2-5 minut)")
    print("  📊 Sprawdź wyniki w UI: http://localhost:5173")
    print()
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
