# Study Designer Chat - Plan Implementacji i Status

**Feature:** Interaktywne Projektowanie Badań przez Chat (inspirowane Claude Code Plan Mode)
**Start:** 2025-11-08
**Target:** Pełna funkcjonalność produkcyjna

---

## 🎯 Vision: Stan Idealny

### User Experience
- [ ] User klika "Nowe Badanie przez Chat" z dashboardu
- [ ] Otwiera się chat interface z welcome message od AI
- [ ] AI zadaje pytania jak doświadczony badacz (quiz-style)
- [ ] User odpowiada naturalnym językiem
- [ ] AI doprecyzowuje wymagania dynamicznie (follow-up questions)
- [ ] Po zebraniu informacji AI generuje szczegółowy plan badania
- [ ] User przegląda plan (markdown z estymacjami kosztów/czasu)
- [ ] User zatwierdza → badanie wykonuje się automatycznie
- [ ] Real-time progress updates podczas wykonania
- [ ] Po zakończeniu: pełne wyniki badania dostępne

### Technical Excellence
- [ ] LangGraph state machine z 7 nodes (welcome → execution)
- [ ] Gemini 2.5 Flash dla generacji pytań (temp=0.8, kreatywność)
- [ ] Gemini 2.5 Flash dla generacji planu (temp=0.3, precision)
- [ ] Structured output parsing (JSON z LLM)
- [ ] Persistent state w PostgreSQL + Redis cache
- [ ] WebSocket dla real-time chat (opcjonalnie REST fallback)
- [ ] Async/await throughout (FastAPI + SQLAlchemy 2.0)
- [ ] Comprehensive error handling i retry logic
- [ ] Usage tracking (tokens, cost, latency)
- [ ] 85%+ test coverage

---

## 📊 Progress Tracker

### Backend (6/32 tasków - 19%)

#### 1. Database Layer (6/6) ✅
- [x] Stworzyć `app/models/study_designer.py`
  - [x] Model `StudyDesignerSession` (id, user_id, project_id, status, conversation_state, generated_plan, created_workflow_id)
  - [x] Model `StudyDesignerMessage` (id, session_id, role, content, metadata)
  - [x] Enums: `SessionStatusEnum`, `MessageRoleEnum`, `ConversationStageEnum`
  - [x] Relationships z User, Project, Workflow
  - [x] Indexes dla performance
- [x] Dodać do `app/models/__init__.py` importy
- [x] Wygenerować migrację Alembic: revision `8ba3d04beee1`
- [x] Przejrzeć i edytować migrację (ręcznie utworzono pełną migrację)
- [ ] Zastosować migrację: `alembic upgrade head` (wymaga Docker environment)
- [ ] Zweryfikować schema w PostgreSQL (wymaga Docker environment)

#### 2. LangGraph State Machine (0/10)
- [ ] Zainstalować zależności: `pip install langgraph`
- [ ] Stworzyć `app/services/study_designer/__init__.py`
- [ ] Stworzyć `app/services/study_designer/state_schema.py`
  - [ ] TypedDict `ConversationState` z wszystkimi polami
  - [ ] Helper functions: serialize/deserialize state
- [ ] Stworzyć `app/services/study_designer/nodes/__init__.py`
- [ ] Stworzyć node executors:
  - [ ] `nodes/welcome.py` - welcome message
  - [ ] `nodes/gather_goal.py` - zbiera cel badania
  - [ ] `nodes/define_audience.py` - definiuje grupę docelową
  - [ ] `nodes/select_method.py` - wybór metody badawczej
  - [ ] `nodes/configure_details.py` - szczegóły konfiguracji
  - [ ] `nodes/generate_plan.py` - generuje plan badania
  - [ ] `nodes/await_approval.py` - czeka na zatwierdzenie
- [ ] Stworzyć `app/services/study_designer/state_machine.py`
  - [ ] `ConversationStateMachine` klasa
  - [ ] Zdefiniować StateGraph z wszystkimi nodes
  - [ ] Conditional routing logic
  - [ ] Compile graph
- [ ] Unit testy state machine (transitions, routing)

#### 3. LLM Integration (0/6)
- [ ] Stworzyć prompty w `config/prompts/study_designer/`
  - [ ] `welcome.yaml` - welcome message
  - [ ] `gather_goal.yaml` - ekstraktuje cel + follow-up
  - [ ] `define_audience.yaml` - ekstraktuje demographics + follow-up
  - [ ] `select_method.yaml` - proponuje metody + wybór
  - [ ] `configure_details.yaml` - zbiera szczegóły
  - [ ] `generate_plan.yaml` - tworzy pełny plan w markdown
- [ ] Dodać do `config/models.yaml` sekcję `study_designer`
- [ ] Stworzyć `app/services/study_designer/question_generator.py`
  - [ ] Generuje follow-up questions bazując na odpowiedziach
  - [ ] Używa Gemini 2.5 Flash (temp=0.8)
  - [ ] Structured output parsing (JSON)
- [ ] Stworzyć `app/services/study_designer/plan_generator.py`
  - [ ] Generuje szczegółowy plan badania
  - [ ] Używa Gemini 2.5 Flash (temp=0.3)
  - [ ] Tworzy WorkflowCreate compatible data
  - [ ] Estymuje czas i koszt
- [ ] Unit testy LLM services (z mock LLM)
- [ ] Integration testy (prawdziwe LLM calls)

#### 4. Orchestrator Service (0/5)
- [ ] Stworzyć `app/services/study_designer/orchestrator.py`
  - [ ] Klasa `StudyDesignerOrchestrator`
  - [ ] `create_session(user_id, project_id)` - rozpoczyna sesję
  - [ ] `process_user_message(session_id, message)` - przetwarza wiadomość
  - [ ] `get_session(session_id)` - pobiera sesję z historią
  - [ ] `approve_plan(session_id)` - zatwierdza i wykonuje
  - [ ] `cancel_session(session_id)` - anuluje sesję
- [ ] Integracja z state machine
- [ ] Persist state do DB po każdej wiadomości
- [ ] Redis cache dla active sessions (1h TTL)
- [ ] Unit testy orchestratora

#### 5. Execution Integration (0/3)
- [ ] Stworzyć `app/services/study_designer/executor.py`
  - [ ] `StudyExecutor` klasa
  - [ ] Konwersja generated_plan → Workflow
  - [ ] Trigger WorkflowExecutor (istniejący)
  - [ ] Real-time progress tracking
- [ ] Error handling podczas execution
- [ ] Integration testy (pełny flow: chat → plan → execute)

#### 6. API Endpoints (0/7)
- [ ] Stworzyć `app/api/study_designer.py`
  - [ ] Router setup
  - [ ] `POST /study-designer/sessions` - create session
  - [ ] `GET /study-designer/sessions/{id}` - get session
  - [ ] `POST /study-designer/sessions/{id}/message` - send message
  - [ ] `POST /study-designer/sessions/{id}/approve` - approve plan
  - [ ] `DELETE /study-designer/sessions/{id}` - cancel session
  - [ ] `GET /study-designer/sessions` - list user sessions
- [ ] Schemas w `app/schemas/study_designer.py`
  - [ ] `SessionCreate`, `SessionResponse`
  - [ ] `MessageSend`, `MessageResponse`
  - [ ] `PlanApproval`
- [ ] Dodać router do `app/main.py`
- [ ] Authorization (JWT, user ownership)
- [ ] Error handling i validation
- [ ] API docs (docstrings, OpenAPI)
- [ ] Integration testy API endpoints

---

### Frontend (0/18 tasków)

#### 7. Chat UI Components (0/8)
- [ ] Stworzyć `frontend/src/components/study-designer/ChatInterface.tsx`
  - [ ] Main chat container
  - [ ] Session initialization
  - [ ] Message state management
  - [ ] WebSocket/REST integration
- [ ] Stworzyć `frontend/src/components/study-designer/MessageList.tsx`
  - [ ] Message rendering (user/assistant)
  - [ ] Markdown support (ReactMarkdown)
  - [ ] Auto-scroll to bottom
  - [ ] Typing indicator
- [ ] Stworzyć `frontend/src/components/study-designer/UserInput.tsx`
  - [ ] Input field + send button
  - [ ] Enter to send (Shift+Enter for newline)
  - [ ] Disabled state podczas loading
- [ ] Stworzyć `frontend/src/components/study-designer/PlanPreview.tsx`
  - [ ] Plan display (markdown)
  - [ ] Estymacje (czas, koszt)
  - [ ] Action buttons (approve, modify, cancel)
- [ ] Stworzyć `frontend/src/components/study-designer/ProgressIndicator.tsx`
  - [ ] Wizard steps (1/6, 2/6, etc.)
  - [ ] Stage names
  - [ ] Visual progress bar
- [ ] Stworzyć `frontend/src/components/study-designer/ExecutionProgress.tsx`
  - [ ] Real-time execution progress
  - [ ] Steps breakdown (generacja person, dyskusja, analiza)
  - [ ] Success/error states
- [ ] Styling (Tailwind CSS, shadcn/ui)
- [ ] Responsive design (mobile, tablet, desktop)

#### 8. State Management & API (0/5)
- [ ] Stworzyć `frontend/src/hooks/useStudyDesigner.ts`
  - [ ] TanStack Query hooks
  - [ ] `useCreateSession`
  - [ ] `useSendMessage`
  - [ ] `useGetSession`
  - [ ] `useApprovePlan`
- [ ] Stworzyć `frontend/src/api/studyDesigner.ts`
  - [ ] API client functions
  - [ ] Error handling
  - [ ] TypeScript types
- [ ] WebSocket integration (opcjonalnie)
- [ ] Optimistic updates
- [ ] Error boundaries

#### 9. Navigation & Integration (0/5)
- [ ] Dodać "Nowe Badanie przez Chat" button do dashboardu
- [ ] Routing dla `/study-designer/:sessionId`
- [ ] Breadcrumbs navigation
- [ ] Przejście do wyników po execution
- [ ] Help/onboarding tooltips

---

### Configuration & Infrastructure (0/8 tasków)

#### 10. Configuration Files (0/4)
- [ ] Dodać sekcję do `config/models.yaml`
  - [ ] `study_designer.question_generation`
  - [ ] `study_designer.plan_generation`
- [ ] Dodać sekcję do `config/features.yaml`
  - [ ] `study_designer.enabled: true`
  - [ ] `study_designer.max_active_sessions_per_user: 3`
  - [ ] `study_designer.session_timeout_minutes: 60`
- [ ] Walidacja: `python scripts/config_validate.py`
- [ ] Dokumentacja w `config/README.md`

#### 11. Testing (0/4)
- [ ] Unit testy backend (services, nodes, parsers)
  - [ ] Target: 85%+ coverage
  - [ ] Mock LLM responses
- [ ] Integration testy backend (API, DB, LLM)
  - [ ] Pełny conversation flow
  - [ ] Error scenarios
- [ ] Frontend component testy (React Testing Library)
  - [ ] Chat interactions
  - [ ] Message rendering
- [ ] E2E testy (Playwright/Cypress)
  - [ ] Happy path: chat → plan → approve → execute
  - [ ] Error handling

---

### Documentation (0/6 tasków)

#### 12. Documentation (0/6)
- [ ] Zaktualizować `docs/BACKEND.md`
  - [ ] Study Designer architecture
  - [ ] State machine flow
  - [ ] API endpoints
- [ ] Zaktualizować `docs/AI_ML.md`
  - [ ] LangGraph integration
  - [ ] Prompty Study Designer
  - [ ] Model selection rationale
- [ ] Zaktualizować `docs/FRONTEND.md` (jeśli istnieje)
  - [ ] Chat UI components
  - [ ] State management
- [ ] User guide w `docs/STUDY_DESIGNER_USER_GUIDE.md`
  - [ ] Jak używać chatu
  - [ ] Przykłady konwersacji
  - [ ] Best practices
- [ ] Zaktualizować `CLAUDE.md`
  - [ ] Informacje o nowej funkcji
  - [ ] Development guidelines
- [ ] Zaktualizować `docs/README.md`
  - [ ] Link do STUDY_DESIGNER_USER_GUIDE.md

---

## 🚀 Quick Start (po implementacji)

```bash
# 1. Zastosuj migracje
docker-compose exec api alembic upgrade head

# 2. Zrestartuj API
docker-compose restart api

# 3. Frontend automatycznie wykryje nowy endpoint

# 4. Użycie
# - Wejdź na dashboard
# - Kliknij "Nowe Badanie przez Chat"
# - Prowadź konwersację z AI
# - Zatwierdź plan
# - Obserwuj wykonanie
```

---

## 📈 Success Metrics

### Functionality
- [ ] User może rozpocząć sesję chatu
- [ ] AI zadaje intelligent follow-up questions
- [ ] Plan jest szczegółowy i profesjonalny
- [ ] Execution działa end-to-end
- [ ] Real-time progress updates działają
- [ ] Error handling jest robust

### Performance
- [ ] Latency LLM response: < 3s (p95)
- [ ] Session creation: < 500ms
- [ ] Plan generation: < 5s
- [ ] Full chat→execute: < 10 min (dla 20 person focus group)

### Quality
- [ ] 85%+ test coverage
- [ ] Zero critical bugs
- [ ] TypeScript strict mode (0 errors)
- [ ] Linting passes (ruff, eslint)

---

## 🎨 Design References

### Conversation Flow Pattern
```
Welcome → Gather Goal → Define Audience → Select Method
→ Configure Details → Generate Plan → Await Approval → Execute
```

### State Machine Nodes
1. **welcome** - Powitanie i rozpoczęcie
2. **gather_goal** - Zbieranie celu badania
3. **define_audience** - Definicja grupy docelowej
4. **select_method** - Wybór metody (personas/focus group/survey)
5. **configure_details** - Szczegóły konfiguracji
6. **generate_plan** - Generacja planu
7. **await_approval** - Czekanie na zatwierdzenie

### Conditional Routing
- Po `gather_goal`: jeśli cel niejasny → loop back, jeśli OK → next
- Po `select_method`: różne nodes w zależności od metody
- Po `await_approval`: approve → execute, modify → configure_details, reject → END

---

## 🔥 Known Challenges & Solutions

### Challenge 1: LLM Hallucinations
**Problem:** LLM może generować niepoprawne estymacje kosztów/czasu
**Solution:** Structured output + post-processing validation

### Challenge 2: Long Conversations
**Problem:** Token limit może być przekroczony w długich rozmowach
**Solution:** Summarization + context window management

### Challenge 3: State Persistence
**Problem:** Session state może być duży (>100KB)
**Solution:** PostgreSQL JSON + Redis cache

### Challenge 4: Error Recovery
**Problem:** Co jeśli LLM call failuje w środku konwersacji?
**Solution:** Retry logic + save state after each message + graceful degradation

---

## 📝 Notes

- Wszystko po polsku (UI, messages, dokumentacja)
- Kod po angielsku (konwencja projektu)
- Używamy istniejących serwisów: WorkflowExecutor, PersonaService, FocusGroupService
- Integracja z istniejącym Workflow systemem (tworzymy Workflow po approval)
- Usage tracking dla kosztów LLM (jak w innych serwisach)

---

**Last Updated:** 2025-11-08
**Status:** 🔴 Not Started (0/96 tasków completed)

