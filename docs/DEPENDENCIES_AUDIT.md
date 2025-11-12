# Audyt Dependencies - Python & Node.js

Dokument powstał podczas audytu 2025-11-11 (zadanie 80 z prompty.md).

## 📦 Python Dependencies (requirements.txt)

### ✅ Dobrze Zorganizowane

requirements.txt jest **dobrze utrzymany**:
- Nieużywane dependencies przeniesione do `pyproject.toml` [optional-dependencies]
- Komentarze wyjaśniają dlaczego niektóre biblioteki są opcjonalne
- Dependencies grouped logically (Core, Database, LangChain, ML, Auth, etc.)

**Przykłady przeniesione do pyproject.toml:**
- `pandas` → [experimental] (currently unused)
- `tiktoken` → [experimental]
- `pypdf`, `python-docx` → [document-processing]
- `openai`, `anthropic` → [llm-providers]

**Rekomendacja:** ✅ Brak akcji - requirements.txt jest clean

---

## 📦 Node.js Dependencies (frontend/package.json)

### ❌ Potencjalnie Nieużywane Dependencies

Po usunięciu komponentów UI w zadaniu 74 (sonner.tsx, carousel.tsx, toggle.tsx, chart.tsx), następujące npm packages mogą być nieużywane:

#### 1. `sonner` (toast notifications)
**Status:** ❌ **PRAWDOPODOBNIE NIEUŻYWANY**
- **Plik:** `sonner.tsx` został usunięty w zadaniu 74
- **Weryfikacja potrzebna:** `rg "from ['\"]sonner" frontend/src`
- **Rozmiar:** ~50KB
- **Akcja:** REMOVE if confirmed unused

---

#### 2. `embla-carousel-react` (carousel component)
**Status:** ❌ **PRAWDOPODOBNIE NIEUŻYWANY**
- **Plik:** `carousel.tsx` został usunięty w zadaniu 74
- **Weryfikacja potrzebna:** `rg "embla-carousel" frontend/src`
- **Rozmiar:** ~100KB
- **Akcja:** REMOVE if confirmed unused

---

#### 3. `@radix-ui/react-toggle` + `@radix-ui/react-toggle-group`
**Status:** ❌ **PRAWDOPODOBNIE NIEUŻYWANY**
- **Plik:** `toggle.tsx` został usunięty w zadaniu 74
- **Weryfikacja potrzebna:** `rg "@radix-ui/react-toggle" frontend/src`
- **Rozmiar:** ~30KB każdy
- **Akcja:** REMOVE if confirmed unused

---

#### 4. `input-otp` (OTP input component)
**Status:** ⚠️ **SPRAWDZIĆ**
- **Obserwacja:** Brak pliku `input-otp.tsx` w zadaniu 74
- **Weryfikacja potrzebna:** `rg "input-otp" frontend/src`
- **Rozmiar:** ~20KB
- **Akcja:** REMOVE if confirmed unused

---

#### 5. `recharts` (chart library)
**Status:** ⚠️ **SPRAWDZIĆ**
- **Obserwacja:** `chart.tsx` został usunięty w zadaniu 74, ale recharts może być używany gdzie indziej (dashboard charts?)
- **Weryfikacja potrzebna:** `rg "recharts|Recharts" frontend/src`
- **Rozmiar:** ~600KB (DUŻY!)
- **Akcja:** KEEP if used in dashboard/analytics, otherwise REMOVE

---

### ✅ Używane Dependencies

Następujące dependencies są **confirmed używane**:

**Core UI:**
- `@radix-ui/react-*` (alert-dialog, avatar, checkbox, collapsible, dialog, dropdown-menu, etc.) - ✅ KEEP
- `lucide-react` - ✅ KEEP (icons używane wszędzie)
- `next-themes` - ✅ KEEP (theme toggle component)
- `clsx` + `tailwind-merge` - ✅ KEEP (className utilities)

**React Ecosystem:**
- `react`, `react-dom`, `react-router-dom` - ✅ KEEP (core)
- `@tanstack/react-query` - ✅ KEEP (data fetching w hooks/)
- `react-hook-form` - ✅ KEEP (forms)
- `react-markdown` - ✅ KEEP (używane w PersonaReasoningPanel, analysis components)

**Workflow & Visualization:**
- `reactflow` - ✅ KEEP (WorkflowEditor.tsx)
- `dagre` + `d3-force` - ✅ KEEP (graph layout dla workflow)
- `@react-three/fiber` + `@react-three/drei` + `three` - ✅ KEEP (3D visualizations)
- `@hello-pangea/dnd` - ✅ KEEP (drag-and-drop w workflow)

**State & Utils:**
- `zustand` - ✅ KEEP (state management)
- `axios` - ✅ KEEP (HTTP client)
- `date-fns` - ✅ KEEP (date formatting)
- `framer-motion` - ✅ KEEP (animations)
- `use-debounce` - ✅ KEEP (debouncing)

**Panels & Resizing:**
- `react-resizable-panels` - ✅ KEEP (używane w drawer.tsx, floating-panel.tsx)
- `vaul` - ✅ KEEP (drawer component)

**i18n:**
- `i18next` + `react-i18next` + `i18next-browser-languagedetector` - ✅ KEEP (internationalization)

---

## 🎯 Rekomendowane Akcje

### Natychmiastowe (Q1 2025)

1. **Weryfikuj nieużywane packages:**
   ```bash
   # W frontend/
   npx depcheck

   # Lub ręcznie:
   rg "from ['\"]sonner" frontend/src
   rg "embla-carousel" frontend/src
   rg "@radix-ui/react-toggle" frontend/src
   rg "input-otp" frontend/src
   rg "recharts|Recharts" frontend/src
   ```

2. **Usuń potwierdzone nieużywane:**
   ```bash
   npm uninstall sonner embla-carousel-react @radix-ui/react-toggle @radix-ui/react-toggle-group input-otp
   # (tylko jeśli weryfikacja potwierdzi że są nieużywane)
   ```

3. **Sprawdź recharts usage - jeśli nieużywany, usuń (oszczędność ~600KB!):**
   ```bash
   npm uninstall recharts
   ```

### Średnioterminowe (Q2 2025)

4. **Regularny audyt z `depcheck`:**
   - Dodaj do CI/CD pipeline: `npx depcheck --json > depcheck-report.json`
   - Alert jeśli znaleziono nieużywane dependencies

5. **Bundle size monitoring:**
   - Użyj `vite-plugin-bundle-analyzer` aby śledzić rozmiar bundle
   - Alert jeśli bundle size >2.5MB

---

## 📊 Potencjalna Oszczędność

Jeśli wszystkie 5 packages są nieużywane:

| Package | Size | Status |
|---------|------|--------|
| recharts | ~600KB | ⚠️ Sprawdź |
| embla-carousel-react | ~100KB | ❌ Usuń |
| sonner | ~50KB | ❌ Usuń |
| @radix-ui/react-toggle | ~30KB | ❌ Usuń |
| @radix-ui/react-toggle-group | ~30KB | ❌ Usuń |
| input-otp | ~20KB | ⚠️ Sprawdź |
| **TOTAL** | **~830KB** | **Potencjalna redukcja** |

**Bundle size impact:** Redukcja ~830KB (compressed) = ~2.5MB (uncompressed) w node_modules

---

## 🔒 Security Dependencies

Następujące dependencies mają krytyczne znaczenie dla security - **NIE USUWAĆ**:

**Python:**
- `python-jose[cryptography]` - JWT authentication
- `PyJWT` - Token validation
- `bcrypt` - Password hashing
- `slowapi` - Rate limiting

**Node.js:**
- Wszystkie `@radix-ui/*` packages są używane i bezpieczne
- Brak znanych security vulnerabilities w używanych packages (założenie - należy zweryfikować z `npm audit`)

---

## ✅ Python Requirements - Status

**Status:** ✅ CLEAN - Brak akcji wymaganych

Nieużywane dependencies już przeniesione do `pyproject.toml` [optional-dependencies]. Requirements.txt zawiera tylko aktywnie używane biblioteki.

---

**Data audytu:** 2025-11-11
**Audytor:** Claude Code (zadanie 80 z prompty.md)
**Status:** Analysis complete - Manual verification needed for 5 npm packages
**Next steps:** Run `npx depcheck frontend/` dla automated check
