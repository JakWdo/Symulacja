# 🇵🇱 Instrukcja - Market Research SaaS

Platforma AI do badań rynkowych wykorzystująca **LangChain + Google Gemini** do generowania statystycznie reprezentatywnych person syntetycznych.

---

## 🚀 Szybki Start (Pełna Aplikacja - 1 Komenda)

### Wymagania
- **Docker Desktop** (zainstaluj z https://www.docker.com/products/docker-desktop/)
- **Klucz API Google AI**

### Instalacja i Uruchomienie

```bash
# 1. Zdobądź klucz API Google AI
# Link: https://ai.google.dev/gemini-api/docs/api-key

# 2. Konfiguracja środowiska
cp .env.example .env
# Edytuj .env i dodaj: GOOGLE_API_KEY=twoj_klucz_tutaj

# 3. Uruchom całą aplikację (backend + frontend + bazy danych)
./start.sh
```

**To wszystko!** Aplikacja będzie dostępna pod:
- **🌐 Frontend UI**: http://localhost:5173
- **🔧 Backend API**: http://localhost:8000
- **📚 API Docs**: http://localhost:8000/docs

### Zatrzymanie Aplikacji

```bash
docker compose down
```

---

## 🛠️ Instalacja Deweloperska (Bez Dockera)

Jeśli chcesz uruchomić aplikację lokalnie bez Dockera:

```bash
# 1-2. Jak wyżej (klucz API + .env)

# 3. Uruchom bazy danych w Docker
docker compose up -d postgres redis neo4j

# 4. Zainstaluj zależności Python
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 5. Zainicjuj bazę danych
python scripts/init_db.py

# 6. Uruchom backend (osobne okno terminala)
uvicorn app.main:app --reload

# 7. Uruchom frontend (osobne okno terminala)
cd frontend
npm install
echo "VITE_API_BASE_URL=http://localhost:8000" > .env
npm run dev
```

**Backend**: http://localhost:8000/docs
**Frontend**: http://localhost:5173

---

## 🔑 Jak Zdobyć Klucze API

### Google AI (Gemini) - WYMAGANE

1. Wejdź: https://ai.google.dev/gemini-api/docs/api-key
2. Kliknij "Get API Key"
3. Skopiuj klucz (AIza...)
4. Dodaj do .env: GOOGLE_API_KEY=twoj_klucz

**Darmowy tier**: 15 requestów/min
**Docs**: https://ai.google.dev/gemini-api/docs


## 📋 Funkcje

- Generowanie Person (Big Five + Hofstede)
- Event Sourcing z pamięcią
- Grupy Fokusowe (100+ person, <30s)
- Detekcja Polaryzacji
- Tryb Adversarialny

---

## 📚 Dokumentacja

- English: README.md
- Gemini API: https://ai.google.dev/gemini-api/docs
- LangChain: https://python.langchain.com/

---

**LangChain + Google Gemini** 🚀
