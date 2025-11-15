#!/usr/bin/env python3
"""
Script do tworzenia danych demonstracyjnych dla platformy Sight w Cloud Run.

Wersja Cloud Run z parametryzacją, retry logic i lepszym loggingiem.
"""

import asyncio
import httpx
import argparse
import sys
from typing import Dict, List, Optional
from datetime import datetime

# Domyślne wartości
DEFAULT_API_BASE = "https://sight-193742683473.europe-central2.run.app/api/v1"
DEFAULT_EMAIL = "demo@sight.pl"
DEFAULT_PASSWORD = "Demo2025!Sight"

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# Account configurations for two separate demo accounts
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


class CloudDemoCreator:
    """Klasa do tworzenia danych demo w Cloud Run."""

    def __init__(self, api_base: str, email: str, password: str):
        self.api_base = api_base
        self.email = email
        self.password = password
        self.token: Optional[str] = None
        self.headers: Dict[str, str] = {"Content-Type": "application/json"}
        self.team_id: Optional[str] = None  # Cached team ID

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

    async def ensure_account_exists(self, client: httpx.AsyncClient, full_name: str, preferred_language: str = 'pl') -> bool:
        """
        Upewnia się że konto istnieje - jeśli nie, rejestruje nowe konto.

        Args:
            client: HTTP client
            full_name: Pełna nazwa użytkownika
            preferred_language: Preferowany język ('pl' lub 'en')

        Returns:
            True jeśli konto istnieje lub zostało utworzone, False w przypadku błędu
        """
        # Próba logowania
        if await self.login(client):
            return True

        print(f"  → Konto nie istnieje, tworzę nowe konto: {self.email}")

        # Rejestracja nowego konta
        for attempt in range(MAX_RETRIES):
            try:
                response = await client.post(
                    f"{self.api_base}/auth/register",
                    json={
                        "email": self.email,
                        "password": self.password,
                        "full_name": full_name,
                        "preferred_language": preferred_language
                    },
                    timeout=30.0
                )

                if response.status_code in [200, 201]:
                    print(f"  ✓ Konto utworzone: {self.email}")

                    # Ponowne logowanie
                    return await self.login(client)
                elif response.status_code == 409:
                    print(f"  ⚠ Konto już istnieje (konflikt), próbuję zalogować...")
                    return await self.login(client)
                else:
                    print(f"  ⚠ Registration attempt {attempt + 1} failed: {response.status_code}")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY)
            except Exception as e:
                print(f"  ⚠ Registration error (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY)

        print(f"  ✗ Nie udało się utworzyć konta po {MAX_RETRIES} próbach")
        return False

    async def ensure_team(self, client: httpx.AsyncClient) -> bool:
        """
        Upewnia się że user ma team - jeśli nie, tworzy domyślny team.

        Returns:
            True jeśli team istnieje lub został utworzony, False w przypadku błędu
        """
        print(f"🏢 Sprawdzanie team dla {self.email}...")

        # Sprawdź czy user ma jakiś team
        try:
            response = await client.get(
                f"{self.api_base}/teams/my",
                headers=self.headers,
                timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()
                teams = data.get('teams', [])

                if teams:
                    self.team_id = teams[0]['id']
                    print(f"  ✓ Znaleziono team: {teams[0]['name']} (ID: {self.team_id})")
                    return True
                else:
                    print(f"  → Brak teamów, tworzę domyślny team...")
            else:
                print(f"  ⚠ Błąd sprawdzania teamów: {response.status_code}")
        except Exception as e:
            print(f"  ⚠ Błąd sprawdzania teamów: {e}")

        # Utwórz domyślny team
        for attempt in range(MAX_RETRIES):
            try:
                response = await client.post(
                    f"{self.api_base}/teams",
                    json={
                        "name": "Demo Team",
                        "description": "Automatycznie utworzony team dla konta demonstracyjnego"
                    },
                    headers=self.headers,
                    timeout=30.0
                )

                if response.status_code in [200, 201]:
                    team = response.json()
                    self.team_id = team['id']
                    print(f"  ✓ Utworzono team: {team['name']} (ID: {self.team_id})")
                    return True
                else:
                    print(f"  ⚠ Create team attempt {attempt + 1}: {response.status_code}")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY)
            except Exception as e:
                print(f"  ⚠ Create team error (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY)

        print(f"  ✗ Nie udało się utworzyć team")
        return False

    async def create_environment(self, client: httpx.AsyncClient, name: str, description: str) -> Optional[str]:
        """Tworzy environment dla team."""
        if not self.team_id:
            print(f"  ✗ Brak team_id - nie można utworzyć environment")
            return None

        for attempt in range(MAX_RETRIES):
            try:
                response = await client.post(
                    f"{self.api_base}/environments",
                    json={
                        "team_id": self.team_id,
                        "name": name,
                        "description": description
                    },
                    headers=self.headers,
                    timeout=30.0
                )

                if response.status_code in [200, 201]:
                    env = response.json()
                    print(f"  ✓ Utworzono environment: {env['name']}")
                    return env['id']
                else:
                    print(f"  ⚠ Create environment attempt {attempt + 1}: {response.status_code}")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY)
            except Exception as e:
                print(f"  ⚠ Create environment error (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY)

        return None

    async def create_project(self, client: httpx.AsyncClient, data: Dict) -> Optional[str]:
        """Tworzy projekt i zwraca ID."""
        for attempt in range(MAX_RETRIES):
            try:
                response = await client.post(
                    f"{self.api_base}/projects",
                    json=data,
                    headers=self.headers,
                    timeout=60.0
                )

                if response.status_code in [200, 201]:
                    result = response.json()
                    print(f"✓ Utworzono projekt: {result['name']} (ID: {result['id']})")
                    return result['id']
                else:
                    print(f"⚠ Create project attempt {attempt + 1}: {response.status_code}")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY)
            except Exception as e:
                print(f"⚠ Create project error (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY)

        return None

    async def generate_personas(self, client: httpx.AsyncClient, project_id: str, num: int) -> bool:
        """
        Generuje persony (background task).

        use_rag=True: Persony będą miały szczegółowe reasoning z orchestration (Neo4j Graph RAG)
        - segment społeczny z charakterystykami
        - graph insights z polskich raportów demograficznych
        - allocation reasoning (dlaczego osoba trafiła do tego segmentu)
        """
        data = {"num_personas": num, "adversarial_mode": False, "use_rag": True}

        for attempt in range(MAX_RETRIES):
            try:
                response = await client.post(
                    f"{self.api_base}/projects/{project_id}/personas/generate",
                    json=data,
                    headers=self.headers,
                    timeout=60.0
                )

                if response.status_code in [200, 202]:
                    print(f"  → Generowanie {num} person uruchomione (background)")
                    return True
                else:
                    print(f"⚠ Generate personas attempt {attempt + 1}: {response.status_code}")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY)
            except Exception as e:
                print(f"⚠ Generate personas error (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY)

        return False

    async def wait_for_personas(self, client: httpx.AsyncClient, project_id: str, expected: int, max_wait: int = 300) -> int:
        """Czeka aż persony się wygenerują (z dłuższym timeoutem dla Cloud Run - 5 min)."""
        print(f"  Czekam na wygenerowanie {expected} person (max {max_wait}s)...")

        for i in range(max_wait):
            await asyncio.sleep(1)

            try:
                response = await client.get(
                    f"{self.api_base}/projects/{project_id}/personas",
                    headers=self.headers,
                    timeout=30.0
                )

                if response.status_code == 200:
                    personas = response.json()
                    count = len(personas)

                    if count >= expected:
                        print(f"  ✓ Wygenerowano {count} person")
                        return count

                    if i % 15 == 0 and i > 0:
                        print(f"    ... {count}/{expected} person (czas: {i}s)")
            except Exception as e:
                if i % 30 == 0 and i > 0:
                    print(f"    ... sprawdzanie statusu ({i}s): {e}")

        # Finalnie sprawdź ile jest
        try:
            response = await client.get(
                f"{self.api_base}/projects/{project_id}/personas",
                headers=self.headers,
                timeout=30.0
            )
            if response.status_code == 200:
                count = len(response.json())
                print(f"  ⚠ Wygenerowano {count}/{expected} person (timeout)")
                return count
        except Exception as e:
            print(f"  ✗ Błąd sprawdzania statusu person: {e}")

        return 0

    async def create_survey(self, client: httpx.AsyncClient, project_id: str, data: Dict) -> Optional[str]:
        """Tworzy ankietę."""
        for attempt in range(MAX_RETRIES):
            try:
                response = await client.post(
                    f"{self.api_base}/projects/{project_id}/surveys",
                    json=data,
                    headers=self.headers,
                    timeout=60.0
                )

                if response.status_code in [200, 201]:
                    result = response.json()
                    print(f"  ✓ Utworzono ankietę: {result['title']}")
                    return result['id']
                else:
                    print(f"⚠ Create survey attempt {attempt + 1}: {response.status_code}")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY)
            except Exception as e:
                print(f"⚠ Create survey error (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY)

        return None

    async def run_survey(self, client: httpx.AsyncClient, survey_id: str) -> bool:
        """Uruchamia zbieranie odpowiedzi ankiety."""
        for attempt in range(MAX_RETRIES):
            try:
                response = await client.post(
                    f"{self.api_base}/surveys/{survey_id}/run",
                    headers=self.headers,
                    timeout=60.0
                )

                if response.status_code in [200, 202]:
                    print(f"  → Zbieranie odpowiedzi uruchomione (background)")
                    return True
                else:
                    print(f"⚠ Run survey attempt {attempt + 1}: {response.status_code}")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY)
            except Exception as e:
                print(f"⚠ Run survey error (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY)

        return False

    async def create_focus_group(self, client: httpx.AsyncClient, project_id: str, data: Dict, persona_ids: List[str]) -> Optional[str]:
        """Tworzy focus group."""
        fg_data = data.copy()
        fg_data['persona_ids'] = persona_ids[:min(len(persona_ids), 10)]

        for attempt in range(MAX_RETRIES):
            try:
                response = await client.post(
                    f"{self.api_base}/projects/{project_id}/focus-groups",
                    json=fg_data,
                    headers=self.headers,
                    timeout=60.0
                )

                if response.status_code in [200, 201]:
                    result = response.json()
                    print(f"  ✓ Utworzono focus group: {result['name']}")
                    return result['id']
                else:
                    print(f"⚠ Create focus group attempt {attempt + 1}: {response.status_code}")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY)
            except Exception as e:
                print(f"⚠ Create focus group error (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY)

        return None

    async def run_focus_group(self, client: httpx.AsyncClient, fg_id: str) -> bool:
        """Uruchamia symulację focus group."""
        for attempt in range(MAX_RETRIES):
            try:
                response = await client.post(
                    f"{self.api_base}/focus-groups/{fg_id}/run",
                    headers=self.headers,
                    timeout=60.0
                )

                if response.status_code in [200, 202]:
                    print(f"  → Symulacja focus group uruchomiona (background)")
                    return True
                else:
                    print(f"⚠ Run focus group attempt {attempt + 1}: {response.status_code}")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY)
            except Exception as e:
                print(f"⚠ Run focus group error (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY)

        return False

    async def create_complete_project(self, client: httpx.AsyncClient, project_def: Dict) -> bool:
        """Tworzy kompletny projekt z personami, ankietami i focus groups."""
        print(f"\n{'='*70}")
        print(f"PROJEKT: {project_def['name']}")
        print(f"{'='*70}")

        # 1. Utwórz environment dla projektu
        env_name = f"Środowisko: {project_def['name'][:50]}"
        env_desc = f"Środowisko dla projektu badawczego: {project_def['name']}"
        environment_id = await self.create_environment(client, env_name, env_desc)

        if not environment_id:
            print(f"  ⚠ Nie udało się utworzyć environment, kontynuuję bez niego...")

        # 2. Utwórz projekt (z przypisaniem do environment jeśli istnieje)
        project_data = {
            "name": project_def['name'],
            "description": project_def['description'],
            "target_audience": project_def['target_audience'],
            "research_objectives": project_def['research_objectives'],
            "target_sample_size": project_def['target_sample_size'],
            "target_demographics": project_def['target_demographics']
        }

        # Dodaj environment_id jeśli został utworzony
        if environment_id:
            project_data["environment_id"] = environment_id

        project_id = await self.create_project(client, project_data)
        if not project_id:
            print(f"✗ Nie udało się utworzyć projektu")
            return False

        # 2. Generuj persony
        if not await self.generate_personas(client, project_id, project_def['num_personas']):
            print(f"✗ Nie udało się uruchomić generacji person")
            return False

        persona_count = await self.wait_for_personas(client, project_id, project_def['num_personas'], max_wait=120)

        if persona_count < 5:
            print(f"  ⚠ Za mało person ({persona_count}), pomijam ankiety i focus groups")
            return False

        # Pobierz IDs person
        try:
            response = await client.get(
                f"{self.api_base}/projects/{project_id}/personas",
                headers=self.headers,
                timeout=30.0
            )
            personas = response.json()
            persona_ids = [p['id'] for p in personas]
        except Exception as e:
            print(f"✗ Błąd pobierania person: {e}")
            return False

        # 3. Utwórz ankiety
        survey_count = 0
        for survey_def in project_def.get('surveys', []):
            survey_id = await self.create_survey(client, project_id, survey_def)
            if survey_id:
                if await self.run_survey(client, survey_id):
                    survey_count += 1
                await asyncio.sleep(2)

        # 4. Utwórz focus groups
        fg_count = 0
        for fg_def in project_def.get('focus_groups', []):
            fg_id = await self.create_focus_group(client, project_id, fg_def, persona_ids)
            if fg_id:
                if await self.run_focus_group(client, fg_id):
                    fg_count += 1
                await asyncio.sleep(2)

        print(f"\n✓ Projekt '{project_def['name']}' ukończony!")
        print(f"  - {persona_count} person")
        print(f"  - {survey_count}/{len(project_def.get('surveys', []))} ankiet")
        print(f"  - {fg_count}/{len(project_def.get('focus_groups', []))} focus groups")

        return True


# DEFINICJE PROJEKTÓW (identyczne jak w lokalnej wersji)
PL_PROJECTS = [
    {
        "name": "Kampania Profilaktyki Zdrowia Psychicznego",
        "description": "Badanie barier w dostępie do terapii i postrzegania zdrowia psychicznego wśród młodych Polaków. Cel: kampania edukacyjna zmniejszająca stygmatyzację.",
        "target_audience": "Polacy 20-40 lat, mieszkańcy dużych miast, różne poziomy wykształcenia",
        "research_objectives": "1) Zidentyfikować bariery w szukaniu pomocy terapeutycznej, 2) Poznać postrzeganie zdrowia psychicznego, 3) Zbadać skuteczność różnych kanałów komunikacji, 4) Opracować kampanię edukacyjną",
        "target_sample_size": 12,
        "target_demographics": {
            "age": {"20-24": 0.25, "25-29": 0.30, "30-34": 0.25, "35-40": 0.20},
            "gender": {"male": 0.45, "female": 0.50, "non-binary": 0.05},
            "location": {"Warszawa": 0.30, "Kraków": 0.25, "Wrocław": 0.20, "Gdańsk": 0.15, "Poznań": 0.10},
            "education": {"Średnie": 0.15, "Wyższe licencjackie": 0.40, "Wyższe magisterskie": 0.45}
        },
        "num_personas": 12,
        "surveys": [
            {
                "title": "Bariery w dostępie do terapii",
                "description": "Ankieta o przeszkodach w szukaniu pomocy psychologicznej i terapeutycznej",
                "questions": [
                    {"id": "q1", "type": "multiple-choice", "title": "Co powstrzymuje Cię przed szukaniem pomocy terapeutycznej?", "options": ["Koszt", "Czas/dostępność", "Wstyd/stygmatyzacja", "Nie wiem gdzie szukać", "Nie uważam że potrzebuję", "Brak wsparcia rodziny"], "required": True},
                    {"id": "q2", "type": "rating-scale", "title": "Oceń swoją wiedzę o dostępnych formach wsparcia (1-10)", "scaleMin": 1, "scaleMax": 10, "required": True},
                    {"id": "q3", "type": "single-choice", "title": "Czy kiedykolwiek rozważałeś/aś terapię?", "options": ["Tak, jestem/byłem w terapii", "Tak, ale nigdy nie podjąłem kroku", "Nie, ale myślałem o tym", "Nie, nigdy"], "required": True},
                    {"id": "q4", "type": "open-text", "title": "Co pomogłoby Ci w podjęciu decyzji o terapii?", "required": False}
                ],
                "target_responses": 500
            },
            {
                "title": "Postrzeganie zdrowia psychicznego",
                "description": "Badanie postaw społecznych wobec zdrowia psychicznego i terapii",
                "questions": [
                    {"id": "q1", "type": "rating-scale", "title": "Jak postrzegasz osoby korzystające z terapii? (1=negatywnie, 10=pozytywnie)", "scaleMin": 1, "scaleMax": 10, "required": True},
                    {"id": "q2", "type": "multiple-choice", "title": "Z jakich źródeł czerpiesz wiedzę o zdrowiu psychicznym?", "options": ["Social media", "Media tradycyjne", "Rozmowy z bliskimi", "Literatura specjalistyczna", "Własne doświadczenia", "Szkoła/uczelnia"], "required": True},
                    {"id": "q3", "type": "single-choice", "title": "Czy rozmawiasz otwarcie o swoim zdrowiu psychicznym?", "options": ["Tak, ze wszystkimi", "Tak, z wybranymi osobami", "Raczej nie", "Absolutnie nie"], "required": True},
                    {"id": "q4", "type": "open-text", "title": "Co powinno się zmienić w społeczeństwie, żeby mówić łatwiej o zdrowiu psychicznym?", "required": False}
                ],
                "target_responses": 500
            }
        ],
        "focus_groups": [
            {
                "name": "Jak zachęcić młodych do szukania pomocy?",
                "description": "Dyskusja o kampaniach edukacyjnych i zmniejszaniu stygmatyzacji",
                "questions": [
                    "Jakie kampanie społeczne dotyczące zdrowia psychicznego zapamietałeś/aś?",
                    "Co najbardziej powstrzymuje młodych przed szukaniem pomocy?",
                    "Jak powinna wyglądać skuteczna kampania edukacyjna?"
                ],
                "mode": "normal"
            }
        ]
    },
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
                    {"id": "q1", "type": "single-choice", "title": "Jak często korzystasz z transportu publicznego?", "options": ["Codziennie", "Kilka razy w tygodniu", "Raz w tygodniu", "Rzadziej", "Wcale"], "required": True},
                    {"id": "q2", "type": "multiple-choice", "title": "Jakie problemy napotykasz najczęściej?", "options": ["Opóźnienia", "Przepełnienie", "Brak połączeń", "Złe oznakowanie", "Brud", "Cena"], "required": True},
                    {"id": "q3", "type": "rating-scale", "title": "Oceń jakość komunikacji miejskiej w Twoim mieście (1-10)", "scaleMin": 1, "scaleMax": 10, "required": True},
                    {"id": "q4", "type": "open-text", "title": "Co najbardziej zachęciłoby Cię do częstszego korzystania z transportu publicznego?", "required": False}
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
    }
]

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
                    {"id": "q1", "type": "single-choice", "title": "How comfortable are you discussing mental health at work?", "options": ["Very comfortable", "Somewhat comfortable", "Neutral", "Somewhat uncomfortable", "Very uncomfortable"], "required": True},
                    {"id": "q2", "type": "multiple-choice", "title": "What prevents you from seeking mental health support?", "options": ["Stigma", "Cost", "Time", "Don't know where to start", "Fear of career impact", "None"], "required": True},
                    {"id": "q3", "type": "rating-scale", "title": "Rate your company's mental health support (1-10)", "scaleMin": 1, "scaleMax": 10, "required": True},
                    {"id": "q4", "type": "open-text", "title": "What would make you more likely to seek mental health support?", "required": False}
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
                    {"id": "q1", "type": "rating-scale", "title": "How safe do you feel in your neighborhood? (1-10)", "scaleMin": 1, "scaleMax": 10, "required": True},
                    {"id": "q2", "type": "rating-scale", "title": "How much do you trust local authorities? (1-10)", "scaleMin": 1, "scaleMax": 10, "required": True},
                    {"id": "q3", "type": "multiple-choice", "title": "What safety issues concern you most?", "options": ["Crime", "Traffic safety", "Public health", "Environmental hazards", "Emergency preparedness"], "required": True},
                    {"id": "q4", "type": "open-text", "title": "What would increase your trust in local authorities?", "required": False}
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


async def main():
    """Główna funkcja - tworzy dane demo w Cloud Run."""
    parser = argparse.ArgumentParser(description='Tworzy dane demo w Cloud Run dla Sight')
    parser.add_argument('--api-base', default=DEFAULT_API_BASE, help='Cloud Run API base URL')
    parser.add_argument('--account-type', choices=['pl', 'intl', 'both'], default='both',
                       help='Typ konta: pl (polskie), intl (międzynarodowe), both (oba)')

    args = parser.parse_args()

    print("="*70)
    print("TWORZENIE DANYCH DEMO W CLOUD RUN - SIGHT")
    print("="*70)
    print(f"API: {args.api_base}")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Tryb: {args.account_type}")
    print("="*70)
    print()

    # Określ które konta tworzyć
    accounts_to_setup = []
    if args.account_type in ['pl', 'both']:
        accounts_to_setup.append('pl')
    if args.account_type in ['intl', 'both']:
        accounts_to_setup.append('intl')

    total_success = 0
    total_expected = 0
    account_results = {}

    async with httpx.AsyncClient(timeout=300.0) as client:
        for account_type in accounts_to_setup:
            config = ACCOUNT_CONFIGS[account_type]

            print(f"\n{'='*70}")
            print(f"KONTO: {config['email']}")
            print(f"Opis: {config['description']}")
            print(f"Język: {config['preferred_language']}")
            print(f"{'='*70}\n")

            # Utwórz creator dla tego konta
            creator = CloudDemoCreator(args.api_base, config['email'], config['password'])

            # Ensure account exists (register if needed)
            if not await creator.ensure_account_exists(client, config['full_name'], config['preferred_language']):
                print(f"\n✗ Nie udało się zapewnić konta {config['email']} - pomijam to konto")
                account_results[config['email']] = {'success': 0, 'expected': 0, 'error': 'Account setup failed'}
                continue

            print()

            # Ensure team exists (required for environments)
            if not await creator.ensure_team(client):
                print("\n⚠ Nie udało się zapewnić team - environments nie będą utworzone")
                # Kontynuuj mimo braku team (projekty można tworzyć bez environment)

            print()

            # Determine which projects to create for this account
            if account_type == 'pl':
                account_projects = PL_PROJECTS
            else:  # intl
                account_projects = INTL_PROJECTS

            print(f"📊 Projektów do utworzenia dla {config['email']}: {len(account_projects)}")
            print(f"⏱ Szacowany czas: ~{len(account_projects) * 3} minut")
            print()

            # Create projects for this account
            success_count = 0
            for i, project_def in enumerate(account_projects, 1):
                print(f"\n[{i}/{len(account_projects)}]")
                try:
                    if await creator.create_complete_project(client, project_def):
                        success_count += 1
                    await asyncio.sleep(5)  # Przerwa między projektami
                except Exception as e:
                    print(f"✗ Błąd przy tworzeniu projektu: {e}")
                    continue

            # Track results for this account
            account_results[config['email']] = {
                'success': success_count,
                'expected': len(account_projects),
                'error': None
            }
            total_success += success_count
            total_expected += len(account_projects)

            print(f"\n{'='*70}")
            print(f"✓ UKOŃCZONO KONTO: {config['email']}")
            print(f"{'='*70}")
            print(f"Utworzono {success_count}/{len(account_projects)} projektów pomyślnie")
            print()

    # Final summary
    print("\n" + "="*70)
    print(f"✓ PODSUMOWANIE FINALNE")
    print("="*70)
    print(f"Ogólny wynik: {total_success}/{total_expected} projektów utworzonych pomyślnie")
    print()
    print("Szczegóły per konto:")
    for email, result in account_results.items():
        if result['error']:
            print(f"  ✗ {email}: {result['error']}")
        else:
            print(f"  ✓ {email}: {result['success']}/{result['expected']} projektów")
    print()
    print("Dostęp do platformy:")
    print(f"  Frontend: {args.api_base.replace('/api/v1', '')}")
    print()
    for account_type in accounts_to_setup:
        config = ACCOUNT_CONFIGS[account_type]
        print(f"  Konto {account_type.upper()}:")
        print(f"    Email: {config['email']}")
        print(f"    Hasło: {config['password']}")
    print("="*70)

    return 0 if total_success == total_expected else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
