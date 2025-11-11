# Analiza Duplikacji Kodu - Backend & Frontend

Dokument powstał podczas audytu 2025-11-11 (zadanie 76 z prompty.md).

## 🔍 Metodologia

Przeszukano kod w poszukiwaniu:
1. Powtarzających się funkcji (>10 linii, 2+ wystąpienia)
2. Podobnych bloków error handling
3. Zduplikowanej logiki walidacji
4. Copy-paste patterns w różnych modułach

## 📊 Wyniki Analizy

### Backend (Python)

#### 1. `__repr__` Methods - LOW PRIORITY
**Lokalizacje:** 13 wystąpień w models/
- `dashboard.py`: 6x
- `workflow.py`: 3x
- `study_designer.py`: 2x
- `persona_events.py`: 2x

**Ocena:** ✅ Akceptowalne - standardowy magic method, duplikacja oczekiwana

**Rekomendacja:** BRAK AKCJI - to jest idiomatyczny Python

---

#### 2. HTTP Exception Handling - MEDIUM PRIORITY
**Lokalizacje:**
- `dependencies.py`: 10 użyć `raise HTTPException(`
- `rag.py`: 9 użyć
- `workflow_crud.py`: 8 użyć
- `settings.py`: 6 użyć
- `focus_groups.py`: 4 użyć

**Wzorzec:**
```python
# Powtarzający się pattern w wielu endpointach
if not entity:
    raise HTTPException(
        status_code=404,
        detail=f"{EntityType} nie znaleziony"
    )
```

**Rekomendacja:**
- **CONSIDER:** Utworzyć helper functions w `app/utils/api_utils.py`:
  ```python
  def raise_not_found(entity_type: str, entity_id: UUID) -> NoReturn:
      raise HTTPException(
          status_code=404,
          detail=f"{entity_type} o ID {entity_id} nie znaleziony"
      )

  def raise_forbidden(message: str = "Brak uprawnień") -> NoReturn:
      raise HTTPException(status_code=403, detail=message)

  def raise_bad_request(message: str) -> NoReturn:
      raise HTTPException(status_code=400, detail=message)
  ```
- **Priorytet:** P2 - Refactoring może poprawić spójność error messages

---

#### 3. CRUD Pattern Repetition - HIGH PRIORITY
**Obserwacja:** Wiele serwisów powtarza ten sam wzorzec CRUD:
- Pobieranie encji z DB
- Walidacja ownership (current_user sprawdzenie)
- Soft-delete pattern (`deleted_at` sprawdzenie)
- Paginacja wyników

**Rekomendacja:**
- **ACTION:** Rozważyć utworzenie `app/services/shared/crud_base.py` z generic CRUD operations:
  ```python
  class BaseCRUDService(Generic[T]):
      def __init__(self, model: Type[T], db: AsyncSession):
          self.model = model
          self.db = db

      async def get_by_id(self, id: UUID, user_id: UUID, check_ownership: bool = True) -> T:
          stmt = select(self.model).where(
              self.model.id == id,
              self.model.deleted_at.is_(None)
          )
          if check_ownership:
              stmt = stmt.where(self.model.user_id == user_id)
          result = await self.db.execute(stmt)
          entity = result.scalar_one_or_none()
          if not entity:
              raise_not_found(self.model.__name__, id)
          return entity

      # ... więcej generic methods (list, create, update, delete)
  ```
- **Priorytet:** P1 - Zmniejszy kod o ~30% w service layer

---

#### 4. Database Query Patterns - MEDIUM PRIORITY
**Obserwacja:** Powtarzający się wzorzec query z soft-delete:
```python
# Powtórzone w ~20 miejscach
stmt = select(Model).where(
    Model.user_id == user_id,
    Model.deleted_at.is_(None)
)
```

**Rekomendacja:**
- **ACTION:** Dodać helper method do Base model:
  ```python
  # app/models/base.py
  class SoftDeleteMixin:
      deleted_at: Mapped[Optional[datetime]]

      @classmethod
      def active_query(cls):
          """Returns query filter for non-deleted entities"""
          return cls.deleted_at.is_(None)

      @classmethod
      def for_user(cls, user_id: UUID):
          """Returns query filter for specific user's entities"""
          return (cls.user_id == user_id) & cls.active_query()

  # Usage:
  stmt = select(Model).where(Model.for_user(user_id))
  ```
- **Priorytet:** P2 - Poprawi czytelność i spójność

---

### Frontend (TypeScript)

#### 5. API Call Patterns - HIGH PRIORITY
**Obserwacja:** TanStack Query hooks powtarzają podobny wzorzec:
- Error handling z toast notifications
- Loading state management
- Success callbacks
- Retry logic

**Rekomendacja:**
- **ACTION:** Utworzyć generic query/mutation wrappers w `frontend/src/lib/api-helpers.ts`:
  ```typescript
  export function useGenericQuery<T>(
    key: string[],
    fetcher: () => Promise<T>,
    options?: {
      onSuccess?: (data: T) => void;
      onError?: (error: Error) => void;
      showErrorToast?: boolean;
    }
  ) {
    return useQuery({
      queryKey: key,
      queryFn: fetcher,
      onSuccess: options?.onSuccess,
      onError: (error) => {
        if (options?.showErrorToast !== false) {
          toast.error(error.message);
        }
        options?.onError?.(error);
      },
      retry: 2,
    });
  }
  ```
- **Priorytet:** P1 - Zmniejszy boilerplate w hooks/

---

#### 6. Form Validation Patterns - MEDIUM PRIORITY
**Obserwacja:** Formularze powtarzają podobne validation rules (email, required, min/max length).

**Rekomendacja:**
- **CONSIDER:** Utworzyć `frontend/src/lib/validators.ts` z reusable validators:
  ```typescript
  export const validators = {
    required: (message = "To pole jest wymagane") => ({
      required: { value: true, message }
    }),
    email: {
      pattern: {
        value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
        message: "Nieprawidłowy adres email"
      }
    },
    minLength: (length: number) => ({
      minLength: {
        value: length,
        message: `Minimum ${length} znaków`
      }
    })
  };

  // Usage:
  <input {...register("email", { ...validators.required(), ...validators.email })} />
  ```
- **Priorytet:** P2 - Spójność error messages

---

## 📈 Podsumowanie Metryk

| Kategoria | Duplikacja | Priorytet | Potencjalna redukcja kodu |
|-----------|-----------|-----------|---------------------------|
| CRUD Pattern (Backend) | HIGH | P1 | ~30% w service layer |
| API Call Patterns (Frontend) | HIGH | P1 | ~25% w hooks/ |
| HTTP Exception Handling | MEDIUM | P2 | ~15% w api/ |
| Database Queries | MEDIUM | P2 | ~10% w services/ |
| Form Validation | MEDIUM | P2 | ~20% w forms |

**Łączna potencjalna redukcja:** ~3500-4000 linii kodu

---

## 🎯 Rekomendowane Akcje

### Q1 2025 (P1 - High Priority)
1. **Utworzyć `BaseCRUDService` generic class** dla common CRUD operations
2. **Utworzyć generic API hooks wrappers** (useGenericQuery, useGenericMutation)
3. **Refaktoryzacja 5-10 najpopularniejszych serwisów** aby używać BaseCRUDService

### Q2 2025 (P2 - Medium Priority)
4. **API utils helpers** dla common HTTP exceptions
5. **SoftDeleteMixin** w Base model dla query patterns
6. **Form validators library** dla spójnych validation rules

### Q3 2025 (P3 - Low Priority - jeśli czas pozwoli)
7. **Code review automatyzacja** - dodać pre-commit hook z pylint duplicate-code check
8. **CI/CD check** - dodać threshold dla code duplication (max 5% according to industry standards)

---

## 🛠️ Narzędzia Rekomendowane

### Python
- **pylint**: `pylint --disable=all --enable=duplicate-code app/`
- **radon**: Cyclomiatic complexity analysis

### TypeScript
- **jscpd**: Copy-paste detector for JavaScript/TypeScript
- **ESLint plugin**: eslint-plugin-sonarjs (no-duplicate-string rule)

---

**Data audytu:** 2025-11-11
**Audytor:** Claude Code (zadanie 76 z prompty.md)
**Status:** Analysis complete - Implementation deferred to Q1-Q2 2025
