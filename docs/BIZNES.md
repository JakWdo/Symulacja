# BIZNES.md - Model Biznesowy Platformy Sight

**Dokument:** 2025-11-04 | **Wersja:** 3.1 (Realistic & Concise) | **Status:** Pre-Launch

---

## Executive Summary

**Sight** to platforma SaaS do szybkich badań jakościowych wspierana przez AI. Generujemy statystycznie reprezentatywne persony i przeprowadzamy symulowane grupy fokusowe w 5 minut zamiast 3-4 tygodni, za 5% tradycyjnych kosztów.

**Nie zastępujemy prawdziwych badań** - wzbogacamy je. Product managerowie używają Sight do szybkiej walidacji hipotez (która funkcja? jaki pricing?), a potem weryfikują kluczowe decyzje z prawdziwymi użytkownikami. Jesteśmy pre-research tool, nie replacement.

**Obecny Status:**
- **MVP:** Production-ready (600+ testów, 80%+ coverage)
- **Traction:** $0 MRR - **not launched yet**
- **Team:** 2 founders (technical + product), sweat equity
- **Need:** Market validation (10-20 beta users w 60 dni) → Pre-Seed $200k-250k

**Unit Economics (Conservative):**
- Gross Margin: 87% ($43.50 profit z $50 ARPU)
- LTV/CAC: 4.4 early → 7.0 mature (target >3.0)
- Payback: 2.9 months (industry: 12-18mo)
- Break-even: 521 users, $26k MRR w **M18-24** (realistic z delays)

**Market:** $8.2B TAM (qualitative research), $2.1B SAM (B2B SaaS), targeting $50M ARR w 5 lat (1% SAM).

**The Ask:** Szukamy $200k-250k Pre-Seed @ $10k-15k MRR traction (post-beta validation).

---

## 1. Problem: Research Jest Za Wolny Dla Nowoczesnego Product Development

Product managerka w startupie SaaS serii A musi zwalidować pricing nowej funkcji ($49 vs $99/mo). Ma trzy opcje:

1. **Tradycyjna grupa fokusowa:** $5,000-10,000, 3-4 tygodnie (recruitment, scheduling, moderation, analysis)
2. **Survey (Google Forms):** Szybko, ale płytko - "80% zapłaciłoby" nie mówi *dlaczego* ani *ile*
3. **Przeczucie:** Bezpłatnie, natychmiast, często błędnie

Większość wybiera #2 lub #3 bo #1 jest prohibitively expensive i slow. W miarę jak product velocity w SaaS wzrosła (2-tygodniowe sprinty vs 6-tygodniowe 5 lat temu), 4-tygodniowe research cycles stały się wąskim gardłem.

**Kwantyfikacja problemu:**
- Globalny rynek badań jakościowych: **$8.2B rocznie**
- 60-70% kosztów to ludzka praca (recruitment, moderation, transcription)
- Dla firm <200 osób, tradycyjne metody są nieosiągalne
- Rezultat: Tysiące produktowych decyzji codziennie na podstawie niekompletnych danych

**Sight rozwiązuje to dostarczając "good enough" jakościowe insighty w tempie i po kosztach surveys**, dając product teams szybką walidację przed podjęciem większych decyzji lub uruchomieniem droższych badań z prawdziwymi użytkownikami.

---

## 2. Opportunity: AI Umożliwia Nową Kategorię Research Toolów

Trzy trendy technologiczne zbiegły się w 2024-2025, czyniąc AI-assisted research wykonalnym:

**1. Frontier LLMs osiągnęły <5% hallucination rate** w strukturalnych zadaniach. Gemini 2.5, Claude 3.5 i GPT-4o generują spójny, kontekstowy dialog który naśladuje ludzkie rozmowy przy <$0.10/1M tokens.

**2. Vector search + Graph RAG** umożliwiają osadzanie person AI w prawdziwych danych demograficznych, trendach rynkowych i insightach kulturowych (pgvector, Neo4j).

**3. Product velocity w SaaS podwoiła się** - sprinty skróciły się z 4 do 2 tygodni, czyniąc tradycyjne 4-tygodniowe research niekompatybilne z modern product development.

### Market Size

**TAM: $8.2B** - Global qualitative research (focus groups, interviews, ethnography), rosnąc 6.5% CAGR do 2030.

**SAM: $2.1B** - B2B SaaS companies (25,000 globalnie) z budżetami $50k-150k/rok na research. Zakładając 30% może zostać skierowane w software solutions = $2.1B SAM.

**SOM: $50M (5-year target)** - 1% SAM = 5,000 customers × $10k ARR każdy.

**Geographic Wedge Strategy:**
- **Year 1-2:** Poland/CEE (5% TAM = $410M) - defensible dzięki local data + cultural expertise
- **Year 2-3:** EU + UK (30% TAM = $2.5B) - GDPR compliance + data sovereignty = competitive advantage
- **Year 3-5:** US market (50% TAM = $4.1B) - enter z established EU case studies + IP portfolio

### Why Now?

Moglibyśmy budować Sight 3 lata temu, ale nie byłby feasible:
- Gemini 2.5 osiągnął enterprise reliability tylko w 2024
- Neo4j Graph RAG adoption eksplodował w enterprise SaaS w 2023-2024
- Product teams desperacko potrzebują szybszych research cycles teraz (nie 5 lat temu)

To jest **"Figma moment" dla researchu** - nowa kategoria collaborative, instant qualitative insights.

---

## 3. Solution: AI-Assisted Research w 5 Minut

User definiuje target market (np. "Product managers, 25-45, SaaS, EU"), zadaje research question ("Czy zapłacą $99/mo za AI task suggestions?").

**W 30 sekund:** Sight generuje 20 statystycznie reprezentatywnych person AI (zróżnicowanych po wieku, doświadczeniu, firmie, pain pointach). Każda persona jest zakorzeniona w prawdziwych danych demograficznych, walidowana przez chi-square test.

**W 5 minut:** 20 person odpowiada asynchronicznie na 4 pytania. Gemini 2.5 generuje responses osadzone w demograficznym kontekście każdej persony.

**Output:** Raport z sentiment analysis (65% positive, 25% neutral, 10% skeptical), key objections, pricing sweet spot ($49-69, nie $99), feature requests, verbatim quotes i confidence score (78%).

**Cost:** $0 (free tier) do $5 (Pro tier) vs $5,000-10,000 traditional.

### Technical Differentiation

**1. Segment-Based Generation (Patent Pending)**
Zamiast generować 20 random person i mieć nadzieję na diversity, dzielimy target market na segmenty demograficzne (wiek, seniority, company size) i wymuszamy proporcjonalny rozkład. Walidujemy chi-square testem—ten sam statystyczny standard co academia.

**2. Asynchronous Focus Groups**
Tradycyjne grupy wymagają wszystkich uczestników jednocześnie. Sight generuje responses równolegle (20 person jednocześnie via async Gemini calls) → kompresujemy 90-min dyskusję do 5 min.

**3. Neo4j Graph RAG**
Budujemy knowledge graph łączący tematy, sentiments i relationships w dyskusji. To pozwala na queries typu: "Które persony wspomniały pricing concerns + feature requests?" - insights które tradycyjna analiza tekstu pominie.

### Competitive Positioning

| Feature | Sight | Synthetic Users | Spot AI | Traditional |
|---------|-------|----------------|---------|-------------|
| Time to Insights | **5 min** | 30 min | 15 min | 14-28 days |
| Cost per Study | **$0-5** | $25-50 | $20-40 | $5k-10k |
| Statistical Validation | ✅ Chi-square | ⚠️ Basic | ⚠️ Basic | ✅ Recruiting |
| Graph RAG | ✅ Neo4j | ❌ | ❌ | ❌ |
| Polish/CEE Data | ✅ | ❌ US-only | ❌ US-only | ⚠️ Expensive |
| API Access | ✅ Full | ⚠️ Limited | ✅ | ❌ |
| **Pricing** | **$49-99/mo** | $99-199/mo | $79-149/mo | $5k-10k/session |

**Pozycjonowanie:** Survey platforms dają breadth bez depth. Tradycyjne agencje dają depth bez speed. **Sight daje qualitative depth w quantitative speed + cost.** 90% tańszy niż agencje, 10x szybszy niż surveys, statystycznie rygorystyczny w przeciwieństwie do AI persona toys.

### Long-Term Vision

**Nie zastępujemy prawdziwych badań - wzbogacamy workflow researchu.** Sight jest pre-research tool:
1. Product manager używa Sight do szybkiej walidacji 3 cenowych wariantów ($49/$69/$99)
2. Sight sugeruje $69 jako sweet spot (78% confidence)
3. PM uruchamia traditional research z real users dla finalnej walidacji przed launch

Cel: Uczynić research **ciągłym** (każdy sprint) zamiast **episodic** (raz na kwartał). "Research layer" dla każdego product team w Europie.

---

## 4. Business Model & Economics

### Revenue Model

**Free Tier (Lead Generation):**
- 5 personas/mo, 1 focus group (3 pytania), watermarked reports
- Goal: 1,000 free users → **8-10% conversion** = 80-100 paying (realistic, nie optimistic 12%)

**Pro Tier ($50-100/mo) - Core Business:**
- **Pro Base ($50):** 50 personas, 10 focus groups, full Graph RAG, API 100 req/day
- **Pro Growth ($100):** 200 personas, unlimited groups, 20GB storage, API 500 req/day
- Assumption: 60% start Base, 40% upgrade do Growth w 3-6mo → blended ARPU $70

**Enterprise ($500-2k/mo) - Year 2-3:**
- Unlimited, SSO, on-premise, 99.9% SLA, dedicated AM, custom fine-tuning
- Target ARPU: $1,200/mo
- Realistic timeline: Material revenue dopiero M18-24 (enterprise sales cycles 6-18mo)

**Additional Streams (Post-PMF):**
- API overages: $0.10/1k tokens ponad limit (+5-8% ARPU)
- Professional services: $1k-5k/projekt (consultation dla enterprise)
- Training workshops: $2k-10k/sesja

### Unit Economics

**Revenue:** $50/user/mo (Pro Base, conservative)

**Variable COGS: $6.50/user/mo**
- Gemini API: $6/user (heavy usage buffer - 99th percentile)
  - Persona gen: $0.011, focus groups: $0.023, summaries: $0.10, RAG: $0.0075
- Infrastructure: $0.50/user (marginal cost, scales down @ 1k+ users)

**Gross Profit:** $43.50/user/mo
**Gross Margin:** 87% (vs 75% SaaS median)

**Fixed Costs:** $22,650/mo (Bootstrap M1-12)
- Personnel: $22k (2 founders @ 50% salary + 50% equity)
- Infrastructure base: $150 (Cloud Run, DBs, monitoring)
- Tools: $200 (GitHub, analytics, CRM)
- Legal: $300 (GDPR, accounting)
- Marketing: $1k-5k (scales to 20-25% MRR)

### CAC Evolution (Time-Based, Realistic)

**M1-6 (Cold Start): $120-150**
Paid channels dominują (LinkedIn/Google ads $180 CAC × 60% volume) bo organic potrzebuje 6-12mo momentum.

**M7-12 (PMF Found): $80-100**
Organic/SEO zaczyna przyczyniać się (30% volume), referrals rosną (20%), paid spada do 40%.

**M13-24 (Brand Awareness): $50-70**
Organic/referral dominują (70% volume), paid używany tactically.

### LTV Calculation (Conservative Churn)

**Early Stage (M1-12, 8% churn):**
```
LTV = $50 × 87% × 12.5mo = $544
LTV/CAC = $544 / $125 = 4.4 ✅ (target >3.0)
Payback = $125 / ($50 × 87%) = 2.9mo ✅
```

**Mature (M13-24, 6% churn, $70 ARPU):**
```
LTV = $70 × 88% × 16.7mo = $1,029
LTV/CAC = $1,029 / $70 = 14.7 ✅✅
Payback = $70 / ($70 × 88%) = 1.1mo ✅✅
```

**Assumption changes z wersji 2.1:**
- Obniżono churn projections z 3% mature → 4-6% (realistic dla B2B SaaS)
- LTV/CAC z 33.8 → 14.7 (still excellent, ale nie outlier)

### Break-Even Analysis

```
Revenue = Fixed + Variable Costs
$50 × N = $22,650 + $6.50N
$43.50 × N = $22,650
N = 521 paying users = $26,050 MRR
```

**Realistic Timeline: M18-24** (nie M13-14)
- Z **15-20% MoM growth** (conservative, nie 25-35%)
- Z **8-10% free-to-paid** (top quartile, nie optimistic 12%)
- Accounting dla delays, pivot time, slower ramp

**Scenariusze:**

| Scenario | Fixed | ARPU | Users | MRR | Timeline |
|----------|-------|------|-------|-----|----------|
| **Bootstrap (Conservative)** | $22,650 | $50 | 521 | $26,050 | M20-24 |
| **Pre-Seed Funded** | $25,000 | $50 | 575 | $28,750 | M16-20 |
| **Seed Funded (Aggressive)** | $35,000 | $70 | 597 | $41,790 | M12-16 |

### Capital Requirements

**Phase 1: Bootstrap MVP + Beta (M0-6)**
- Capital: $50k-75k (founder savings)
- Goal: **10-20 beta customers @ $25-50/mo** (proof of payment willingness)
- Validate: <10% churn, >40 NPS, 50%+ activation
- **This is CRITICAL - need traction przed fundraising**

**Phase 2: Pre-Seed (M6-9)** ⭐
- **Raise: $200k-250k za 15-20% equity** (realistic dilucja)
- **Timing: @ $10k-15k MRR** (po beta validation)
- **Valuation: $1.2M-1.5M post-money** (reasonable dla validated B2B SaaS w EU)
- **Use of Funds:**
  - 50% Marketing ($5k-8k/mo paid acquisition)
  - 30% Hiring (first engineer lub designer, CS contractor)
  - 20% Runway buffer (18-month runway do break-even)
- **Investor Profile:** Angel/micro-VC z B2B SaaS experience, hands-off ale strategic
- **Expected Outcome:** Break-even M18-24, $26k MRR

**Phase 3 (M18-30): Profitable Growth**
- Reinvest profits, scale do $100k MRR, prepare Series A

**Phase 4 (M30+): Series A (Optional)**
- Raise $1.5M-3M @ $1.5M ARR
- Use: EU expansion, US entry, enterprise team

**Total Dilution:** Pre-Seed (18%) + Series A (18%) = 36%, founders retain 64%.

---

## 5. Go-To-Market Strategy

### Ideal Customer Profile

**Primary: Product Managers w B2B SaaS (Series A/B)**
- Demografia: 28-38 lat, miasta (Warszawa, Berlin, Amsterdam)
- Firma: 10-200 osób, $2M-10M ARR, funded
- Budget authority: $50-100/mo bez CFO approval
- Pain: Tradycyjne research za wolne (3-4 tygodnie), za drogie ($5k)
- Jobs-to-be-done: Zwalidować features, test pricing, understand user pain points w tempie 2-week sprintów

**Why This ICP:**
1. High intent - już wydają na research
2. Short sales cycle - self-serve, 7-14 dni trial → paid
3. Viral potential - PM communities share tools (Slack, LinkedIn, Twitter)
4. Upsell path - gdy firma rośnie, account grows (Base → Growth → Team → Enterprise)

### Three-Phase GTM

**PHASE 1: Beta Validation (M1-6, 0 → 20 Beta Users)**

**Budget: $1,000/mo**

Channels:
1. **Direct Outreach** - Founders reach 50 PMs tygodniowo via LinkedIn
2. **Product Hunt Soft Launch** - "Private beta" signal, zbierz waitlist
3. **Content** - 2 blog posts/tydzień (longtail keywords: "fast market research," "ai personas")

**Critical Goal: 10-20 paying beta users @ $25-50/mo**
- Proof że ktoś zapłaci
- 3-5 video testimonials
- <10% churn, 50%+ activation

Expected outcome: $500-1k MRR, proof of concept

---

**PHASE 2: Product-Market Fit (M7-12, 20 → 100 Users)**

**Budget: $3,000/mo**

Channels:
1. **LinkedIn Ads** ($1.5k/mo) - Target "Product Manager" + "B2B SaaS," expected CAC $100-120
2. **Google Ads** ($1k/mo) - Keywords: "ai focus groups," "fast qualitative research"
3. **Referral Program** - Launch M6, 10% revenue share dla referrers
4. **SEO Content** ($500/mo) - Outsource 10-15 artykułów/miesiąc do Polski ($20-30/artykuł)

Conversion funnel:
```
1,000 visitors/mo
  → 5-8% signup = 50-80 signups
    → 8-10% paid = 4-8 paying/mo
      → $50 ARPU = $200-400 new MRR/mo
```

Expected outcome: 100 users, $5k MRR, **15-20% MoM growth** (realistic)

---

**PHASE 3: Scale (M13-24, 100 → 500 Users)**

**Budget: $8,000/mo** (reinvested z cash flow positive)

New channels:
1. **Enterprise SDR** (M13) - $4k/mo (base + commission), target 5 enterprise deals do M18
2. **Partnerships** - Product management communities (Mind the Product), sponsored webinars
3. **Integrations** - Notion, Slack, Figma marketplaces (organic discovery)
4. **Customer Success** - Part-time CS manager ($2k/mo), reduce churn 8% → 6%

Expected outcome: 500 users, $25k-30k MRR, approaching break-even

### Message Points Per Channel

**LinkedIn (ROI-focused):**
*"Zwaliduj features 10x szybciej. Sight daje jakościowe insighty w 5 minut - nie 5 tygodni - za 95% niższym koszcie. Używane przez [Company A], [Company B]."*

**Product Hunt (Tech-forward):**
*"Pierwsze statystycznie reprezentatywne AI personas. Chi-square validated, Graph RAG powered, 5-minute research."*

**Blog/SEO (Educational):**
*"Jak zwalidować Twój SaaS pricing w <1 tydzień bez $5k budżetu [Complete Guide]"*

---

## 6. Roadmap

### Year 1 (M1-12): Beta → PMF → Break-Even Approach

**Q1 (M1-3): Beta Launch**
- Ship: MVP (personas, focus groups, basic reporting, free + Pro tiers)
- Goal: 10-20 beta users, $500-1k MRR
- **Validate or pivot:** Jeśli churn >15% lub activation <40% → investigate deeply

**Q2 (M4-6): PMF Optimization**
- Ship: Pro Growth tier, API access, referral program, advanced exports
- Goal: 50-100 users, $3k-5k MRR
- **Fundraising:** Prepare Pre-Seed materials

**Q3 (M7-9): Pre-Seed Close + Scale Foundations**
- Close: $200k-250k Pre-Seed
- Ship: Annual plans, survey builder (new vertical), CEE data expansion
- Ramp marketing: $3k/mo (LinkedIn + Google Ads)
- Goal: 200-300 users, $10k-15k MRR

**Q4 (M10-12): Enterprise Readiness**
- Ship: SSO, advanced security (SOC2 prep), white-label, custom fine-tuning pilot
- Goal: 300-500 users, $15k-25k MRR, clear path do break-even

---

### Year 2 (M13-24): Break-Even → Market Expansion

**Q1: Enterprise Launch**
- Ship: Enterprise tier, on-premise deployment, advanced analytics
- Hire: 1 SDR dla enterprise sales
- Target: 5 enterprise accounts

**Q2: New Product Vertical**
- Ship: Persona Journey Mapping (visualize touchpoints, emotions, pain points)
- Monetize: $20/mo add-on dla Pro users

**Q3: EU Expansion**
- Marketing: German/Dutch markets, localized content
- Ship: German/Netherlands demographic data, multi-currency

**Q4: Integrations & Platform**
- Ship: Zapier, Notion sync, Slack bot, Figma plugin, Public API
- Goal: 2,000-2,500 users, $100k-125k MRR, Series A ready

---

### Year 3-5: Category Leadership

**Strategic Pillars:**
1. **US Market Entry** (M25-36) - US sales team, SaaStr/ProductCon sponsorships
2. **Platform Ecosystem** (M30-48) - Marketplace dla third-party plugins, 70/30 revenue share
3. **Vertical SaaS** (M36-60) - Sight dla Healthcare, FinTech, eCommerce (compliance + industry data)
4. **Enterprise Dominance** - 100+ accounts representing 30-40% MRR

**Vision:** 10,000 users, $600k-800k MRR, $7M-10M ARR do M60.

---

## 7. Metrics, Risks & The Ask

### North Star Metric: MRR

**Milestones:**
```
M6:  $5,000      (100 users, PMF validation)
M12: $15,000     (300 users, halfway do break-even)
M18: $26,000     (520 users, break-even achieved)
M24: $100,000    (2,000 users, Series A ready)
```

### Key Metrics (Grouped)

**Acquisition:**
- New signups: 50-100/mo → 150-250/mo → 300-500/mo
- Free→Pro conversion: 8-10% (realistic)
- Activation rate: 50-60% (complete first focus group w 7 dni)
- CAC: $125 → $80 → $50

**Retention:**
- Monthly churn: 8% → 6% → 4% (conservative)
- NPS: >40
- DAU/MAU: >30%

**Revenue:**
- MRR growth: **15-20% MoM** (realistic, nie optimistic 25-35%)
- ARPU: $50 → $70 → $100+

**Unit Economics:**
- LTV/CAC: 4.4 → 14.7 (excellent, ale nie outlier)
- Payback: 2.9mo → 1.1mo
- Gross Margin: 87-90%

### Critical Risks & Mitigations

**RISK #1: Zero Traction Currently** ⚠️ CRITICAL
- **Problem:** $0 MRR = zero proof ktokolwiek zapłaci
- **Mitigation:** PILNE - 10-20 beta users @ $25-50/mo w next 60 days, 3-5 video testimonials, proof of <10% churn

**RISK #2: LLM Hallucinations Erode Trust** (High Impact)
- **Problem:** Jeśli persona mówi coś offensive/błędne, users tracą zaufanie forever
- **Mitigation:** Chi-square validation, transparency disclaimers ("AI-simulated insights, not real humans"), manual review 5% responses, <2% hallucination threshold

**RISK #3: Google Gemini Vendor Lock-In** (High Impact)
- **Problem:** 100% zależność od Gemini - jeśli Google podniesie ceny 3x, economics upadają
- **Mitigation:** Multi-provider abstraction **W PRODUKCJI przed fundraising** (nie "mamy, ale nie deployed"), demo że możemy swap Gemini ↔ Claude w <2 tygodnie, negotiate fixed pricing @ $5k/mo spend

**RISK #4: Competitive Moat Słaby** (Medium Impact)
- **Problem:** Synthetic Users, Spot AI już istnieją. "Polish data" moat jest łatwy do skopiowania
- **Mitigation:**
  - **Deep partnerships:** White-label deals z Polish research agencies (lock before US competitors)
  - **Exclusive data:** Agreements z GUS, research institutions, universities
  - **Open-source strategy:** Open-source części stacku (community building, hiring advantage)
  - **Platform play:** Integrations + API ecosystem = network effects

**RISK #5: Enterprise Sales Underestimated** (Medium Impact)
- **Problem:** 1 SDR nie zamknie 5-10 enterprise deals. Enterprise sales cycles 6-18mo konfliktują z projected 15-20% MoM growth
- **Mitigation:** Realistic timeline (enterprise revenue material dopiero M18-24), focus M1-12 na SMB self-serve, nie enterprise

**RISK #6: Break-Even Może Zająć Dłużej** (Medium Impact)
- **Problem:** Założenia (15-20% MoM, 8-10% conversion) mogą być optimistic jeśli market nie responds
- **Mitigation:** Scenario planning (worst-case: 10% MoM → M30 break-even), fundraising buffer (raise @ $10k MRR, nie wait do $0), monthly budget review, pivot triggers (<10% MoM dla 3 consecutive months)

### The Ask: Pre-Seed $200k-250k

**Current Status:**
- MVP: Production-ready, $0 MRR (not launched)
- Team: 2 technical founders, sweat equity
- Runway: $50k-75k savings

**Financing Plan:**

**Phase 1 (NOW - M6): Bootstrap Beta**
- Capital: $50k-75k founder savings
- Goal: **10-20 paying beta @ $25-50/mo** = $500-1k MRR
- Proof: <10% churn, >40 NPS, 3-5 testimonials
- **This is CRITICAL - need traction przed fundraising**

**Phase 2 (M6-9): Pre-Seed** ⭐
- **Raise: $200k-250k za 15-20% equity** (realistic dilucja)
- **Timing: @ $10k-15k MRR** (po beta validation)
- **Valuation: $1.2M-1.5M post-money** (reasonable dla validated B2B SaaS w EU)
- **Use of Funds:**
  - 50% Marketing ($5k-8k/mo paid acquisition)
  - 30% Hiring (first engineer lub designer, CS contractor)
  - 20% Runway buffer (18-month runway do break-even)
- **Investor Profile:** Angel/micro-VC z B2B SaaS experience, hands-off ale strategic
- **Expected Outcome:** Break-even M18-24, $26k MRR

**Phase 3 (M18-30): Profitable Growth**
- Reinvest profits, scale do $100k MRR, prepare Series A

**Phase 4 (M30+): Series A (Optional)**
- Raise $1.5M-3M @ $1.5M ARR
- Use: EU expansion, US entry, enterprise team

**Total Dilution:** Pre-Seed (18%) + Series A (18%) = 36%, founders retain 64%.

---

## Wnioski & Realistic Assessment

### Co Wiemy (Strengths)

✅ **Real Problem:** $5k-10k i 3-4 tygodnie na traditional research faktycznie jest barierą
✅ **Solid Tech:** Production-ready MVP (600+ tests), sophisticated stack (Gemini + Neo4j + RAG)
✅ **Excellent Unit Economics:** 87% margin, 2.9mo payback, 4.4 LTV/CAC even w early stage
✅ **Market Timing:** AI research staje się acceptable, product teams potrzebują szybszych cycles
✅ **Professional Execution:** Team jest technical, planning jest thorough

### Czego Nie Wiemy (Risks)

⚠️ **Zero Traction:** $0 MRR = zero proof że ktokolwiek zapłaci. **MUST VALIDATE w next 60 days.**
⚠️ **AI Quality Risk:** Czy AI personas mogą naprawdę dostarczyć wartościowe insighty? Enterprise buyers będą sceptyczni.
⚠️ **Competition:** Synthetic Users ($5M funded), Spot AI już istnieją z podobnym value prop.
⚠️ **Moat Uncertainty:** Polish data nie jest strong defensibility. Potrzeba partnerships + exclusive agreements.
⚠️ **Market Acceptance:** Czy product teams zaakceptują "AI-simulated" insights jako valuable?

### Comparable Trajectories

- **Notion:** $0 → $10M ARR w 4 lata (freemium SaaS)
- **Typeform:** $0 → $70M ARR w 5 lat (survey tool)
- **Figma:** $0 → $75M ARR w 5 lat (collaborative design)

**Sight realistyczny potential:** $10-20M ARR w 5 lat jeśli execution jest excellent i market responds positively. To nie jest unicorn ($1B+), ale może być solid $50-100M exit dla founders i early investors.

### Next 90 Days: Validation Plan

**Week 1-4:**
- [ ] Launch beta @ $25/mo (aggressive discount dla early adopters)
- [ ] Direct outreach: 100 PMs via LinkedIn/email
- [ ] Target: 10 signups, 5 activated (first focus group)

**Week 5-8:**
- [ ] 10 user interviews - czy value prop resonates?
- [ ] Iterate based na feedback
- [ ] Target: 10 paying users, <10% churn

**Week 9-12:**
- [ ] Zbierz 3 video testimonials
- [ ] Metrics dashboard: activation, churn, NPS
- [ ] Prepare Pre-Seed deck z real traction
- [ ] Target: 20 paying, $500-1k MRR, proof of concept

**Jeśli osiągniemy:** → Raise Pre-Seed @ $10k MRR
**Jeśli nie:** → Pivot lub shutdown (better niż burn capital na unvalidated idea)

---

**Dokument:** 2025-11-04 | **Wersja:** 3.1 | **Status:** Pre-Launch, Need Validation

**Changelog v3.1:**
- ✅ Obniżono projekcje (15-20% MoM, 8-10% conversion, M18-24 break-even)
- ✅ Honest o $0 MRR i potrzebie validation
- ✅ Pozycjonowanie: wsparcie researchu, nie zastąpienie
- ✅ Wzmocniono moat (partnerships, data deals, open-source)
- ✅ Realistyczne risk assessment
- ✅ Skrócono o ~30% (999 → 700 linii)
- ✅ Mniej storytellingu, więcej konkretów