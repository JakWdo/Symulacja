#!/usr/bin/env python3
"""
Script do tworzenia danych demonstracyjnych dla platformy Sight.

Tworzy 4 projekty (2 PL + 2 INT) z personami, ankietami i focus groups.
"""

import asyncio
import httpx
import json
from typing import Dict, List, Any

API_BASE = "http://localhost:8000/api/v1"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwZGJkOWVhOS1lMGI4LTRmZTMtYmRjNC1mOTQzYzNjYTBlZjYiLCJlbWFpbCI6ImRlbW9Ac2lnaHQucGwiLCJleHAiOjE3NjI1MDE3NTcsImlhdCI6MTc2MjQ5OTk1N30.NkHMxii7H26BAVdAh_jj4kV7TZW02UE-nD-o4tAqJo8"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}


async def create_project(client: httpx.AsyncClient, data: Dict) -> str:
    """Tworzy projekt i zwraca ID."""
    response = await client.post(f"{API_BASE}/projects", json=data, headers=HEADERS)
    result = response.json()
    print(f"✓ Utworzono projekt: {result['name']} (ID: {result['id']})")
    return result['id']


async def generate_personas(client: httpx.AsyncClient, project_id: str, num: int) -> None:
    """Generuje persony (background task)."""
    data = {"num_personas": num, "adversarial_mode": False, "use_rag": False}
    response = await client.post(
        f"{API_BASE}/projects/{project_id}/personas/generate",
        json=data,
        headers=HEADERS
    )
    print(f"  → Generowanie {num} person uruchomione (background)")


async def wait_for_personas(client: httpx.AsyncClient, project_id: str, expected: int, max_wait: int = 90) -> int:
    """Czeka aż persony się wygenerują."""
    print(f"  Czekam na wygenerowanie {expected} person (max {max_wait}s)...")
    for i in range(max_wait):
        await asyncio.sleep(1)
        response = await client.get(f"{API_BASE}/projects/{project_id}/personas", headers=HEADERS)
        personas = response.json()
        count = len(personas)
        if count >= expected:
            print(f"  ✓ Wygenerowano {count} person")
            return count
        if i % 10 == 0 and i > 0:
            print(f"    ... {count}/{expected} person (czas: {i}s)")

    # Finalnie sprawdź ile jest
    response = await client.get(f"{API_BASE}/projects/{project_id}/personas", headers=HEADERS)
    count = len(response.json())
    print(f"  ⚠ Wygenerowano {count}/{expected} person (timeout)")
    return count


async def create_survey(client: httpx.AsyncClient, project_id: str, data: Dict) -> str:
    """Tworzy ankietę."""
    response = await client.post(
        f"{API_BASE}/projects/{project_id}/surveys",
        json=data,
        headers=HEADERS
    )
    result = response.json()
    print(f"  ✓ Utworzono ankietę: {result['title']}")
    return result['id']


async def run_survey(client: httpx.AsyncClient, survey_id: str) -> None:
    """Uruchamia zbieranie odpowiedzi ankiety."""
    response = await client.post(
        f"{API_BASE}/surveys/{survey_id}/run",
        headers=HEADERS
    )
    print(f"  → Zbieranie odpowiedzi uruchomione (background)")


async def create_focus_group(client: httpx.AsyncClient, project_id: str, data: Dict, persona_ids: List[str]) -> str:
    """Tworzy focus group."""
    data['persona_ids'] = persona_ids[:min(len(persona_ids), 10)]  # Max 10 person
    response = await client.post(
        f"{API_BASE}/projects/{project_id}/focus-groups",
        json=data,
        headers=HEADERS
    )
    result = response.json()
    print(f"  ✓ Utworzono focus group: {result['name']}")
    return result['id']


async def run_focus_group(client: httpx.AsyncClient, fg_id: str) -> None:
    """Uruchamia symulację focus group."""
    response = await client.post(
        f"{API_BASE}/focus-groups/{fg_id}/run",
        headers=HEADERS
    )
    print(f"  → Symulacja focus group uruchomiona (background)")


# DEFINICJE PROJEKTÓW
PROJECTS = [
    # Projekt 2 PL: Transport Miejski
    {
        "name": "Rewolucja Transportu Miejskiego 2025",
        "description": "Badanie potrzeb mieszkańców dużych miast dotyczących komunikacji miejskiej, ekologii i innowacji w transporcie publicznym. Cel: opracowanie rekomendacji dla władz miejskich.",
        "target_audience": "Mieszkańcy dużych miast Polski 20-55 lat, regularni użytkownicy transportu publicznego",
        "research_objectives": "1) Zidentyfikować główne problemy komunikacji miejskiej, 2) Poznać oczekiwania wobec ekologicznego transportu, 3) Zbadać gotowość do zmiany nawyków transportowych, 4) Wypracować rekomendacje dla władz",
        "target_sample_size": 12,
        "target_demographics": {
            "age": {"18-24": 0.20, "25-34": 0.35, "35-44": 0.30, "45-54": 0.15},
            "gender": {"male": 0.48, "female": 0.52},
            "location": {"Warszawa": 0.30, "Kraków": 0.25, "Wrocław": 0.20, "Gdańsk": 0.15, "Poznań": 0.10},
            "education": {"Średnie ogólnokształcące": 0.20, "Wyższe licencjackie": 0.35, "Wyższe magisterskie": 0.45}
        },
        "num_personas": 12,
        "surveys": [
            {
                "title": "Twoje doświadczenia z komunikacją miejską",
                "description": "Ankieta o codziennym korzystaniu z transportu publicznego, problemach i oczekiwaniach",
                "questions": [
                    {
                        "id": "q1",
                        "type": "single-choice",
                        "title": "Jak często korzystasz z transportu publicznego?",
                        "options": ["Codziennie", "Kilka razy w tygodniu", "Raz w tygodniu", "Rzadziej", "Wcale"],
                        "required": True
                    },
                    {
                        "id": "q2",
                        "type": "multiple-choice",
                        "title": "Jakie problemy napotykasz najczęściej?",
                        "options": ["Opóźnienia", "Przepełnienie", "Brak połączeń", "Złe oznakowanie", "Brud", "Cena"],
                        "required": True
                    },
                    {
                        "id": "q3",
                        "type": "rating-scale",
                        "title": "Oceń jakość komunikacji miejskiej w Twoim mieście (1-10)",
                        "scaleMin": 1,
                        "scaleMax": 10,
                        "required": True
                    },
                    {
                        "id": "q4",
                        "type": "open-text",
                        "title": "Co najbardziej zachęciłoby Cię do częstszego korzystania z transportu publicznego?",
                        "required": False
                    }
                ],
                "target_responses": 500
            }
        ],
        "focus_groups": [
            {
                "name": "Jak poprawić transport publiczny?",
                "description": "Dyskusja o innowacjach i zmianach potrzebnych w komunikacji miejskiej",
                "questions": [
                    "Jakie zmiany w transporcie publicznym byłyby dla Ciebie najważniejsze?",
                    "Czy jesteś gotów zapłacić więcej za lepszą jakość usług?",
                    "Jak widzisz przyszłość mobilności miejskiej za 5 lat?"
                ],
                "mode": "normal"
            }
        ]
    },

    # Projekt 3 INT: Mental Health
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

    # Projekt 4 INT: Community Safety
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


async def create_complete_project(client: httpx.AsyncClient, project_def: Dict) -> None:
    """Tworzy kompletny projekt z personami, ankietami i focus groups."""
    print(f"\n{'='*60}")
    print(f"PROJEKT: {project_def['name']}")
    print(f"{'='*60}")

    # 1. Utwórz projekt
    project_data = {
        "name": project_def['name'],
        "description": project_def['description'],
        "target_audience": project_def['target_audience'],
        "research_objectives": project_def['research_objectives'],
        "target_sample_size": project_def['target_sample_size'],
        "target_demographics": project_def['target_demographics']
    }
    project_id = await create_project(client, project_data)

    # 2. Generuj persony
    await generate_personas(client, project_id, project_def['num_personas'])
    persona_count = await wait_for_personas(client, project_id, project_def['num_personas'], max_wait=90)

    # Pobierz IDs person
    response = await client.get(f"{API_BASE}/projects/{project_id}/personas", headers=HEADERS)
    personas = response.json()
    persona_ids = [p['id'] for p in personas]

    if persona_count < 5:
        print(f"  ⚠ Za mało person ({persona_count}), pomijam ankiety i focus groups")
        return

    # 3. Utwórz ankiety
    for survey_def in project_def.get('surveys', []):
        survey_id = await create_survey(client, project_id, survey_def)
        await run_survey(client, survey_id)
        await asyncio.sleep(2)  # Krótka przerwa

    # 4. Utwórz focus groups
    for fg_def in project_def.get('focus_groups', []):
        fg_id = await create_focus_group(client, project_id, fg_def, persona_ids)
        await run_focus_group(client, fg_id)
        await asyncio.sleep(2)

    print(f"✓ Projekt '{project_def['name']}' ukończony!")
    print(f"  - {persona_count} person")
    print(f"  - {len(project_def.get('surveys', []))} ankiet")
    print(f"  - {len(project_def.get('focus_groups', []))} focus groups")


async def main():
    """Główna funkcja - tworzy wszystkie projekty demo."""
    print("="*60)
    print("TWORZENIE DANYCH DEMONSTRACYJNYCH DLA SIGHT")
    print("="*60)
    print(f"Projekty do utworzenia: {len(PROJECTS)}")
    print(f"Szacowany czas: ~{len(PROJECTS) * 2} minut")
    print()

    async with httpx.AsyncClient(timeout=300.0) as client:
        # Projekt 1 już istnieje, więc pomiń
        print("⚠ Projekt 1 (Kampania Profilaktyki Zdrowia Psychicznego) już istnieje - pomijam")

        # Utwórz pozostałe projekty
        for project_def in PROJECTS:
            try:
                await create_complete_project(client, project_def)
                await asyncio.sleep(5)  # Przerwa między projektami
            except Exception as e:
                print(f"✗ Błąd przy tworzeniu projektu: {e}")
                continue

    print("\n" + "="*60)
    print("✓ UKOŃCZONO TWORZENIE DANYCH DEMONSTRACYJNYCH!")
    print("="*60)
    print("\nWszystkie projekty są dostępne w UI platformy Sight.")
    print("Frontend: http://localhost:5173")


if __name__ == "__main__":
    asyncio.run(main())
