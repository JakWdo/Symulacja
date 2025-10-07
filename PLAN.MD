# UI Implementation Plan - Sight Market Research SaaS

## Overview
Align the current UI implementation with the Figma design (sight) while maintaining full backend functionality and real data integration. The UI must look **exactly** like the Figma design.

---

## Task Breakdown

### ✅ 1. Dashboard Charts Redesign [COMPLETED]
**Files:** `frontend/src/components/layout/FigmaDashboard.tsx`

**Current Issues:**
- Bar chart implementation differs from Figma design ✓
- Pie chart rendering needs refinement ✓
- Need to match exact colors, spacing, and styling from Figma ✓

**Actions:**
- [x] Import custom chart components from Figma (CustomBarChart, CustomPieChart)
- [x] Match exact bar heights, widths (38px), gaps (12px), and colors
- [x] Implement proper legend with color swatches below pie chart
- [x] Use real data from backend (maintain current data fetching logic)
- [x] Match exact card styling, borders, shadows from Figma

---

### ✅ 2. Project Detail Page Enhancements [COMPLETED]
**Files:** `frontend/src/components/layout/ProjectDetail.tsx`

**Current Issues:**
- Too many menu options (has Setup, Personas, Focus Groups tabs) ✓
- Missing project details display (Target Audience, Research Objectives, etc.) ✓
- Missing navigation panels to Personas, Focus Groups, Surveys ✓

**Actions:**
- [x] Simplify tab menu to single "Setup" tab only
- [x] Add Target Audience section displaying `project.target_demographics`
- [x] Add Research Objectives, Timeline, Budget fields
- [x] Add "Quick Actions" cards with navigation to:
  - Personas (with Users icon)
  - Focus Groups (with MessageSquare icon)
  - Surveys (with BarChart3 icon)
- [x] Match Figma styling for cards with hover effects
- [x] Connect all fields to real backend data

---

### ✅ 3. Personas Page Filter Fix [COMPLETED]
**Files:** `frontend/src/components/layout/Personas.tsx`

**Current Issues:**
- Page crashes when filters result in zero personas ✓
- Need empty state message ✓

**Actions:**
- [x] Add check for `filteredPersonas.length === 0` after filtering
- [x] Display empty state card: "No personas match the selected filters"
- [x] Add "Clear Filters" button in empty state
- [x] Ensure carousel index resets to 0 when filters change
- [x] Test all filter combinations (gender, age range, occupation)

---

### ✅ 4. Surveys Page Styling Updates [COMPLETED]
**Files:** `frontend/src/components/layout/Surveys.tsx`

**Current Issues:**
- Visual differences from Figma design ✓
- Card layouts and spacing need refinement ✓

**Actions:**
- [x] Match exact card layouts from Figma
- [x] Update progress bars to match Figma styling
- [x] Ensure badge colors match Figma (green for completed, blue for running, etc.)
- [x] Match button styles and positioning
- [x] Verify all icons match Figma design
- [x] Add shadow-sm to all cards
- [x] Update stats cards colors to #F27405

---

### ✅ 5. Focus Groups Major Redesign
**Files:**
- `frontend/src/components/layout/FocusGroups.tsx`
- `frontend/src/components/layout/FocusGroupView.tsx`
- `frontend/src/components/layout/FocusGroupBuilder.tsx` (may need to create)

**Current Issues:**
- Menu/tabs structure differs significantly from Figma
- Run discussion UI needs complete redesign
- Analysis/results view doesn't match Figma
- Missing spinning logo animation during simulation

**Sub-tasks:**

#### 5.1 Focus Groups List Page [COMPLETED]
- [x] Update card layout to match Figma exactly
- [x] Implement proper status badges with Figma colors
- [x] Add configuration button for pending groups
- [x] Update "Create Focus Group" flow
- [x] Add shadow-sm to cards for consistency
- [x] Update stats cards with proper colors (#F27405)

#### 5.2 Focus Group Detail - Configuration Tab [COMPLETED]
- [x] Match Figma layout for questions display
- [x] Add/remove question functionality with proper UI
- [x] Participants selection with checkboxes
- [x] Match card styling and spacing

#### 5.3 Focus Group Detail - Discussion Tab (Run Discussion) [COMPLETED]
- [x] Implement spinning logo animation using `sight-logo-przezroczyste.png`
- [x] Create progress UI matching Figma:
  - Progress bar with percentage
  - Current status messages
  - Status descriptions based on progress
- [x] Match exact colors and spacing from Figma
- [x] Add "Generate AI Summary" button after completion
- [x] Implement AI summary generation flow

#### 5.4 Focus Group Detail - Results & Analysis Tab [COMPLETED]
- [x] Implement toggle between "Responses" and "AI Summary" views
- [x] AI Summary section:
  - Executive Summary card
  - Key Insights card
  - Recommendations card
  - Use AI icon/logo from Figma
- [x] Sentiment Analysis chart:
  - Doughnut/pie chart with proper colors
  - Legend below chart
  - Interactive hover effects
- [x] Score Analysis with ScoreChart component
- [x] Raw Responses accordion:
  - Expandable questions with ChevronDown/Up icons
  - Persona avatars with gradient circles
  - Proper card styling and animations
- [x] Match all animations from Figma (framer-motion)

#### 5.5 Logo Integration [COMPLETED]
- [x] Copy `sight-logo-przezroczyste.png` from sight folder to `frontend/public/`
- [x] Create Logo component for spinning animation
- [x] Use during "Simulation in progress" state
- [x] Apply `animate-spin` class

---

### ✅ 6. Graph Analysis (Future Task - DO NOT IMPLEMENT YET)
**Files:** New component `frontend/src/components/analysis/GraphAnalysis.tsx`

**Note:** Add to plan but DO NOT implement. This will be a future enhancement.

**Actions:**
- [ ] Plan NetworkGraph component structure
- [ ] Design Neo4j integration for persona relationships
- [ ] Create interactive 3D visualization (react-force-graph or similar)
- [ ] Add to navigation when ready

---

## Technical Requirements

### Colors & Theming
- Primary orange: `#F27405`
- Secondary orange: `#F29F05`
- Success green: `#28a745`
- Info blue: `#17a2b8`
- Match all border colors, shadows, and backgrounds from Figma

### Components to Use
- Use existing shadcn/ui components
- Import Figma-generated custom components where needed
- Maintain framer-motion animations
- Use lucide-react icons consistently

### Data Integration
- ALL data must come from backend APIs
- NO mock/dummy data in final implementation
- Maintain existing TanStack Query patterns
- Preserve all existing API calls

### Testing Checklist
- [ ] Test with real backend data
- [ ] Test all filter combinations
- [ ] Test loading states
- [ ] Test error states
- [ ] Test empty states
- [ ] Verify responsive design (mobile, tablet, desktop)
- [ ] Test dark mode compatibility
- [ ] Cross-browser testing

---

## File Structure
```
frontend/src/components/
├── layout/
│   ├── FigmaDashboard.tsx ✏️ Update charts
│   ├── ProjectDetail.tsx ✏️ Major redesign
│   ├── Personas.tsx ✏️ Fix filters
│   ├── Surveys.tsx ✏️ Minor styling
│   ├── FocusGroups.tsx ✏️ Major redesign
│   ├── FocusGroupView.tsx ✏️ Complete overhaul
│   └── FocusGroupBuilder.tsx 🆕 May need to create
├── analysis/
│   ├── AISummaryPanel.tsx ✅ Already exists
│   └── GraphAnalysis.tsx 🔮 Future
└── ui/
    ├── Logo.tsx 🆕 Create spinning logo component
    └── ScoreChart.tsx ✅ Import from Figma

frontend/public/
└── sight-logo-przezroczyste.png 🆕 Copy from sight/
```

---

## Execution Order
1. Dashboard charts (low risk, high visibility)
2. Personas filter fix (bug fix, high priority)
3. Project Detail enhancements (medium complexity)
4. Surveys styling (low complexity)
5. Focus Groups complete redesign (high complexity, most work)
6. Final testing and refinements

---

## Success Criteria
✅ UI matches Figma design pixel-perfect
✅ All functionality works with real backend data
✅ No bugs or crashes when filtering/navigating
✅ Smooth animations and transitions
✅ Responsive across all screen sizes
✅ Dark mode works correctly
