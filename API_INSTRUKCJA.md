# Instrukcja API - Komunikacja z Pythonem

Prosty przewodnik jak korzystać z Market Research SaaS API przy użyciu Pythona.

## 📦 Instalacja

```bash
pip install requests
```

## 🚀 Podstawowa Konfiguracja

```python
import requests
import json
from typing import Dict, List, Optional

# Adres API
BASE_URL = "http://localhost:8000/api/v1"

class MarketResearchAPI:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })

    def _post(self, endpoint: str, data: dict) -> dict:
        """Helper do POST requests"""
        response = self.session.post(f"{self.base_url}{endpoint}", json=data)
        response.raise_for_status()
        return response.json()

    def _get(self, endpoint: str) -> dict:
        """Helper do GET requests"""
        response = self.session.get(f"{self.base_url}{endpoint}")
        response.raise_for_status()
        return response.json()
```

## 📝 Przykłady Użycia

### 1. Utwórz Projekt

```python
def create_project(api: MarketResearchAPI,
                   name: str,
                   description: str,
                   demographics: dict,
                   sample_size: int = 20) -> dict:
    """
    Tworzy nowy projekt badawczy

    Args:
        name: Nazwa projektu
        description: Opis projektu
        demographics: Słownik z rozkładami demograficznymi
        sample_size: Liczba person do wygenerowania

    Returns:
        Dane utworzonego projektu (z project_id)
    """
    data = {
        "name": name,
        "description": description,
        "target_demographics": demographics,
        "target_sample_size": sample_size
    }
    return api._post("/projects", data)


# Przykład użycia
api = MarketResearchAPI()

project = create_project(
    api=api,
    name="Test Nowego Produktu",
    description="Badanie reakcji klientów na nowy produkt tech",
    demographics={
        "age_group": {
            "18-24": 0.3,
            "25-34": 0.5,
            "35-44": 0.2
        },
        "gender": {
            "Male": 0.45,
            "Female": 0.55
        },
        "education_level": {
            "Bachelor's": 0.6,
            "Master's": 0.3,
            "PhD": 0.1
        }
    },
    sample_size=20
)

project_id = project["id"]
print(f"✅ Utworzono projekt: {project_id}")
```

### 2. Wygeneruj Persony

```python
def generate_personas(api: MarketResearchAPI,
                      project_id: str,
                      num_personas: int = 20) -> dict:
    """
    Generuje persony dla projektu

    Args:
        project_id: ID projektu
        num_personas: Liczba person do wygenerowania

    Returns:
        Potwierdzenie rozpoczęcia generowania
    """
    data = {
        "num_personas": num_personas,
        "adversarial_mode": False
    }
    return api._post(f"/projects/{project_id}/personas/generate", data)


# Przykład
response = generate_personas(api, project_id, num_personas=20)
print(f"⏳ Generowanie person: {response['message']}")

# Poczekaj ~30-60s, potem sprawdź status
import time
time.sleep(45)

# Pobierz wygenerowane persony
personas = api._get(f"/projects/{project_id}/personas")
print(f"✅ Wygenerowano {len(personas)} person")
```

### 3. Utwórz Grupę Fokusową

```python
def create_focus_group(api: MarketResearchAPI,
                       project_id: str,
                       name: str,
                       persona_ids: List[str],
                       questions: List[str]) -> dict:
    """
    Tworzy grupę fokusową

    Args:
        project_id: ID projektu
        name: Nazwa grupy fokusowej
        persona_ids: Lista ID person do dołączenia
        questions: Lista pytań do dyskusji

    Returns:
        Dane utworzonej grupy fokusowej
    """
    data = {
        "name": name,
        "description": f"Grupa fokusowa dla projektu {project_id}",
        "persona_ids": persona_ids,
        "questions": questions,
        "mode": "normal"
    }
    return api._post(f"/projects/{project_id}/focus-groups", data)


# Przykład
persona_ids = [p["id"] for p in personas[:10]]  # Wybierz 10 person

focus_group = create_focus_group(
    api=api,
    project_id=project_id,
    name="Sesja #1 - Pierwsze Wrażenia",
    persona_ids=persona_ids,
    questions=[
        "Co sądzisz o tym produkcie?",
        "Jakie funkcje są dla Ciebie najważniejsze?",
        "Ile byłbyś gotów zapłacić?",
        "Co należałoby ulepszyć?"
    ]
)

focus_group_id = focus_group["id"]
print(f"✅ Utworzono grupę fokusową: {focus_group_id}")
```

### 4. Uruchom Dyskusję

```python
def run_focus_group(api: MarketResearchAPI, focus_group_id: str) -> dict:
    """
    Uruchamia dyskusję w grupie fokusowej

    Args:
        focus_group_id: ID grupy fokusowej

    Returns:
        Potwierdzenie rozpoczęcia dyskusji
    """
    return api._post(f"/focus-groups/{focus_group_id}/run", {})


# Przykład
response = run_focus_group(api, focus_group_id)
print(f"⏳ Uruchamianie dyskusji: {response['message']}")

# Poczekaj ~2-5 minut na zakończenie
time.sleep(180)  # 3 minuty

# Sprawdź status
status = api._get(f"/focus-groups/{focus_group_id}")
print(f"Status: {status['status']}")
```

### 5. Pobierz Wyniki

```python
def get_responses(api: MarketResearchAPI, focus_group_id: str) -> dict:
    """Pobiera wszystkie odpowiedzi z grupy fokusowej"""
    return api._get(f"/focus-groups/{focus_group_id}/responses")


def get_insights(api: MarketResearchAPI, focus_group_id: str) -> dict:
    """Pobiera podstawowe metryki i insights"""
    return api._get(f"/focus-groups/{focus_group_id}/insights")


def generate_ai_summary(api: MarketResearchAPI,
                        focus_group_id: str,
                        use_pro_model: bool = False) -> dict:
    """
    Generuje AI summary dyskusji

    Args:
        focus_group_id: ID grupy fokusowej
        use_pro_model: True = Gemini Pro (lepsze), False = Flash (szybsze)
    """
    return api._post(
        f"/focus-groups/{focus_group_id}/ai-summary",
        {},
        params={"use_pro_model": use_pro_model}
    )


# Przykłady
responses = get_responses(api, focus_group_id)
print(f"\n📊 Odpowiedzi: {responses['total_responses']} odpowiedzi")

for q in responses["questions"]:
    print(f"\n❓ {q['question']}")
    print(f"   💬 {len(q['responses'])} odpowiedzi")

insights = get_insights(api, focus_group_id)
print(f"\n📈 Idea Score: {insights['idea_score']:.1f}/100")
print(f"🤝 Consensus: {insights['consensus_level']:.1%}")
print(f"😊 Sentiment: {insights['average_sentiment']:.2f}")

# AI Summary (może potrwać 5-10s)
summary = generate_ai_summary(api, focus_group_id, use_pro_model=False)
print(f"\n📝 Executive Summary:\n{summary['executive_summary']}")
print(f"\n💡 Key Insights:")
for insight in summary['key_insights']:
    print(f"  • {insight}")
```

### 6. Eksportuj Raport PDF

```python
def export_pdf(api: MarketResearchAPI, focus_group_id: str, filename: str):
    """
    Eksportuje raport do PDF

    Args:
        focus_group_id: ID grupy fokusowej
        filename: Nazwa pliku wyjściowego
    """
    response = api.session.get(
        f"{api.base_url}/focus-groups/{focus_group_id}/export/pdf"
    )
    response.raise_for_status()

    with open(filename, 'wb') as f:
        f.write(response.content)

    print(f"✅ Zapisano raport: {filename}")


# Przykład
export_pdf(api, focus_group_id, "raport_badania.pdf")
```

## 🔄 Pełny Workflow

```python
import requests
import time
from typing import List

BASE_URL = "http://localhost:8000/api/v1"

class MarketResearchClient:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def create_project(self, name: str, demographics: dict, sample_size: int = 20):
        """Utwórz projekt"""
        data = {
            "name": name,
            "description": f"Projekt: {name}",
            "target_demographics": demographics,
            "target_sample_size": sample_size
        }
        r = self.session.post(f"{self.base_url}/projects", json=data)
        return r.json()

    def generate_personas(self, project_id: str, num_personas: int = 20):
        """Wygeneruj persony"""
        data = {"num_personas": num_personas, "adversarial_mode": False}
        r = self.session.post(
            f"{self.base_url}/projects/{project_id}/personas/generate",
            json=data
        )
        return r.json()

    def get_personas(self, project_id: str):
        """Pobierz persony"""
        r = self.session.get(f"{self.base_url}/projects/{project_id}/personas")
        return r.json()

    def create_focus_group(self, project_id: str, name: str,
                           persona_ids: List[str], questions: List[str]):
        """Utwórz grupę fokusową"""
        data = {
            "name": name,
            "persona_ids": persona_ids,
            "questions": questions,
            "mode": "normal"
        }
        r = self.session.post(
            f"{self.base_url}/projects/{project_id}/focus-groups",
            json=data
        )
        return r.json()

    def run_focus_group(self, focus_group_id: str):
        """Uruchom dyskusję"""
        r = self.session.post(f"{self.base_url}/focus-groups/{focus_group_id}/run")
        return r.json()

    def get_focus_group_status(self, focus_group_id: str):
        """Sprawdź status"""
        r = self.session.get(f"{self.base_url}/focus-groups/{focus_group_id}")
        return r.json()

    def get_insights(self, focus_group_id: str):
        """Pobierz insights"""
        r = self.session.get(f"{self.base_url}/focus-groups/{focus_group_id}/insights")
        return r.json()

    def generate_summary(self, focus_group_id: str):
        """Wygeneruj AI summary"""
        r = self.session.post(
            f"{self.base_url}/focus-groups/{focus_group_id}/ai-summary",
            params={"use_pro_model": False}
        )
        return r.json()


# === KOMPLETNY PRZYKŁAD ===

def main():
    client = MarketResearchClient()

    # 1. Utwórz projekt
    print("📋 Tworzenie projektu...")
    project = client.create_project(
        name="Test Aplikacji Mobilnej",
        demographics={
            "age_group": {"18-24": 0.4, "25-34": 0.6},
            "gender": {"Male": 0.5, "Female": 0.5}
        },
        sample_size=15
    )
    project_id = project["id"]
    print(f"✅ Projekt utworzony: {project_id}")

    # 2. Wygeneruj persony
    print("\n👥 Generowanie person...")
    client.generate_personas(project_id, num_personas=15)
    print("⏳ Czekam 45s na generowanie...")
    time.sleep(45)

    personas = client.get_personas(project_id)
    print(f"✅ Wygenerowano {len(personas)} person")

    # 3. Utwórz grupę fokusową
    print("\n🎯 Tworzenie grupy fokusowej...")
    persona_ids = [p["id"] for p in personas[:10]]

    focus_group = client.create_focus_group(
        project_id=project_id,
        name="Sesja Testowa",
        persona_ids=persona_ids,
        questions=[
            "Jakie są Twoje pierwsze wrażenia?",
            "Co Ci się najbardziej podoba?",
            "Co należy poprawić?"
        ]
    )
    fg_id = focus_group["id"]
    print(f"✅ Grupa fokusowa: {fg_id}")

    # 4. Uruchom dyskusję
    print("\n💬 Uruchamianie dyskusji...")
    client.run_focus_group(fg_id)
    print("⏳ Czekam 2 minuty na dyskusję...")
    time.sleep(120)

    # 5. Sprawdź status
    status = client.get_focus_group_status(fg_id)
    print(f"Status: {status['status']}")

    if status['status'] == 'completed':
        # 6. Pobierz wyniki
        print("\n📊 Pobieranie wyników...")
        insights = client.get_insights(fg_id)

        print(f"\n📈 WYNIKI:")
        print(f"  Idea Score: {insights['idea_score']:.1f}/100")
        print(f"  Consensus: {insights['consensus_level']:.1%}")
        print(f"  Sentiment: {insights['average_sentiment']:.2f}")

        # 7. AI Summary
        print("\n🤖 Generowanie AI summary...")
        summary = client.generate_summary(fg_id)

        print(f"\n📝 PODSUMOWANIE:")
        print(summary['executive_summary'])

        print(f"\n💡 KLUCZOWE INSIGHTS:")
        for i, insight in enumerate(summary.get('key_insights', []), 1):
            print(f"  {i}. {insight}")
    else:
        print("❌ Dyskusja nie zakończona, spróbuj ponownie później")


if __name__ == "__main__":
    main()
```

## 📊 Asynchroniczne Przetwarzanie

Generowanie person i uruchamianie dyskusji są operacjami asynchronicznymi:

```python
import time

def wait_for_completion(api, check_func, timeout=300, interval=10):
    """
    Czeka na zakończenie operacji asynchronicznej

    Args:
        api: Instancja API
        check_func: Funkcja sprawdzająca status (zwraca dict ze statusem)
        timeout: Maksymalny czas oczekiwania (sekundy)
        interval: Częstotliwość sprawdzania (sekundy)
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        result = check_func()

        if isinstance(result, dict) and result.get('status') == 'completed':
            print("✅ Operacja zakończona!")
            return result

        print(f"⏳ Status: {result.get('status', 'unknown')}, czekam {interval}s...")
        time.sleep(interval)

    raise TimeoutError("Przekroczono czas oczekiwania")


# Przykład użycia
client = MarketResearchClient()

# Uruchom dyskusję
client.run_focus_group(focus_group_id)

# Czekaj na zakończenie
result = wait_for_completion(
    api=client,
    check_func=lambda: client.get_focus_group_status(focus_group_id),
    timeout=300,  # 5 minut
    interval=15   # sprawdzaj co 15s
)

print(f"Dyskusja zakończona w {result['metrics']['total_execution_time_ms']/1000:.1f}s")
```

## 🔍 Obsługa Błędów

```python
import requests
from requests.exceptions import HTTPError, Timeout, ConnectionError

def safe_api_call(func, *args, **kwargs):
    """Wrapper z obsługą błędów"""
    try:
        return func(*args, **kwargs)
    except HTTPError as e:
        if e.response.status_code == 404:
            print(f"❌ Nie znaleziono zasobu: {e.response.url}")
        elif e.response.status_code == 400:
            print(f"❌ Błędne dane: {e.response.json().get('detail')}")
        elif e.response.status_code == 500:
            print(f"❌ Błąd serwera: {e.response.json().get('detail')}")
        else:
            print(f"❌ HTTP Error: {e}")
        return None
    except Timeout:
        print("❌ Timeout - serwer nie odpowiada")
        return None
    except ConnectionError:
        print("❌ Brak połączenia z serwerem")
        return None
    except Exception as e:
        print(f"❌ Nieoczekiwany błąd: {e}")
        return None


# Przykład
project = safe_api_call(
    client.create_project,
    name="Test Project",
    demographics={"age_group": {"18-24": 1.0}},
    sample_size=10
)

if project:
    print(f"✅ Projekt utworzony: {project['id']}")
else:
    print("❌ Nie udało się utworzyć projektu")
```

## 📚 Przydatne Informacje

### Czasy Wykonania
- **Generowanie person**: ~1.5-3s per persona (20 person = ~30-60s)
- **Uruchamianie dyskusji**: ~2-5 minut (zależy od liczby person × pytań)
- **AI Summary**: ~5-10s (Flash), ~10-15s (Pro)

### Limity
- **Maksymalna liczba person w projekcie**: bez limitu (zalecane: 20-50)
- **Maksymalna liczba person w grupie fokusowej**: 100 (zalecane: 5-20)
- **Maksymalna liczba pytań**: bez limitu (zalecane: 3-5)

### Kody Statusu
- `200` - OK
- `201` - Created
- `202` - Accepted (operacja asynchroniczna rozpoczęta)
- `204` - No Content (usunięcie zakończone)
- `400` - Bad Request (błędne dane)
- `404` - Not Found (zasób nie istnieje)
- `500` - Internal Server Error (błąd serwera)

---