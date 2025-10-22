"""
Prompty dla grup fokusowych i podsumowań dyskusji.

Ten moduł zawiera wszystkie prompty używane w procesie symulacji grup fokusowych:
- PERSONA_RESPONSE_PROMPT_TEMPLATE - Odpowiedzi person w dyskusjach
- DISCUSSION_SUMMARY_SYSTEM_PROMPT - System prompt dla AI summarizer
- DISCUSSION_SUMMARY_PROMPT_TEMPLATE - Generowanie podsumowań dyskusji

Użycie:
    from app.core.prompts.focus_group_prompts import PERSONA_RESPONSE_PROMPT_TEMPLATE
"""

# ═══════════════════════════════════════════════════════════════════════════════
# PERSONA RESPONSE PROMPT (FocusGroupServiceLangChain)
# ═══════════════════════════════════════════════════════════════════════════════

PERSONA_RESPONSE_PROMPT_TEMPLATE = """You are participating in a focus group discussion.

PERSONA DETAILS:
Name: {full_name}
Age: {age}, Gender: {gender}
Occupation: {occupation}
Education: {education_level}
Location: {location}

PERSONALITY:
Values: {values}
Interests: {interests}

BACKGROUND:
{background_story}{context_text}

QUESTION: {question}

Respond naturally as this person would in 2-4 sentences. Be authentic and conversational."""

# Retry prompt (jeśli LLM zwróci pustą odpowiedź)
PERSONA_RESPONSE_RETRY_SUFFIX = """

IMPORTANT INSTRUCTION:
- Provide a natural, conversational answer of at least one full sentence.
- Do not return an empty string or placeholders.
- Stay in character as the persona described above."""


def build_persona_response_prompt(
    persona_data: dict,
    question: str,
    context: list = None
) -> str:
    """
    Helper do budowania prompta dla odpowiedzi persony.

    Args:
        persona_data: Dict z danymi persony (full_name, age, gender, etc.)
        question: Pytanie do odpowiedzi
        context: Lista poprzednich interakcji (opcjonalnie)

    Returns:
        Sformatowany prompt
    """
    # Formatuj kontekst poprzednich odpowiedzi (max 3 najbardziej istotne)
    context_text = ""
    if context:
        context_text = "\n\nPast interactions:\n"
        for i, ctx in enumerate(context[:3], 1):
            if ctx.get("event_type") == "response_given":
                event_data = ctx.get("event_data", {})
                context_text += f"{i}. Q: {event_data.get('question', '')}\n"
                context_text += f"   A: {event_data.get('response', '')}\n"

    # Format values and interests (max 4 each)
    values = persona_data.get('values', [])
    values_str = ', '.join(values[:4]) if values else 'Balanced approach to life'

    interests = persona_data.get('interests', [])
    interests_str = ', '.join(interests[:4]) if interests else 'Various interests'

    return PERSONA_RESPONSE_PROMPT_TEMPLATE.format(
        full_name=persona_data.get('full_name', 'Participant'),
        age=persona_data.get('age', '?'),
        gender=persona_data.get('gender', '?'),
        occupation=persona_data.get('occupation', 'Professional'),
        education_level=persona_data.get('education_level', 'Educated'),
        location=persona_data.get('location', 'Urban area'),
        values=values_str,
        interests=interests_str,
        background_story=persona_data.get('background_story', 'Has diverse life experiences'),
        context_text=context_text,
        question=question
    )


def build_fallback_response(persona_data: dict, question: str) -> str:
    """
    Tworzy fallback response gdy LLM nie wygeneruje odpowiedzi.

    Args:
        persona_data: Dict z danymi persony
        question: Pytanie

    Returns:
        Zapasowa odpowiedź
    """
    full_name = persona_data.get('full_name', 'Ta persona')
    name = full_name.split(" ")[0]
    occupation = persona_data.get('occupation', 'uczestnik badania')

    return (
        f"{name}, pracując jako {occupation}, potrzebuje chwili, by uporządkować myśli wokół pytania "
        f"\"{question}\". Zaznacza jednak, że chętnie wróci do tematu, bo uważa go za ważny dla całej dyskusji."
    )


# ═══════════════════════════════════════════════════════════════════════════════
# DISCUSSION SUMMARY PROMPTS (DiscussionSummarizerService)
# ═══════════════════════════════════════════════════════════════════════════════

DISCUSSION_SUMMARY_SYSTEM_PROMPT = """You are a world-class market research analyst specializing in qualitative research synthesis.
Your role is to analyze focus group discussions and generate strategic insights for product teams.

IMPORTANT GUIDELINES:
- Be concise yet comprehensive
- Focus on actionable insights, not just description
- Identify patterns, contradictions, and surprising findings
- Consider demographic differences in opinions
- Provide strategic recommendations grounded in data
- Use professional, business-oriented language
- Avoid generic statements - be specific and evidence-based"""


DISCUSSION_SUMMARY_PROMPT_TEMPLATE = """Analyze this focus group discussion and generate a comprehensive strategic summary.

**FOCUS GROUP TOPIC:** {topic}
**DESCRIPTION:** {description}

{demo_context}

**DISCUSSION TRANSCRIPT:**
{discussion_text}

---

Please provide a detailed analysis in the following structure:

## 1. EXECUTIVE SUMMARY (90-120 words)
Synthesize the core findings into a high-level overview that answers:
- What was the overall reception to the concept/topic?
- What are the most critical takeaways?
- What is the strategic implication?

## 2. KEY INSIGHTS (3-5 bullet points, ≤25 words each)
Surface the most important patterns and themes from the discussion.
Structure every bullet as: **Insight label**: implication grounded in evidence.
Use proper markdown bold syntax: **text** (two asterisks on both sides).
Prioritize by business impact.

## 3. SURPRISING FINDINGS (1-2 bullet points, ≤20 words each)
Highlight unexpected or counterintuitive discoveries that challenge assumptions.
These could be:
- Contradictions between what participants say vs. underlying sentiment
- Minority opinions that reveal edge cases
- Demographic differences that weren't anticipated

## 4. SEGMENT ANALYSIS
Break down how different demographic segments (age, gender, occupation) responded differently.
Structure as:
**Segment name**: Key differentiator with quote/evidence (≤25 words)
Use proper markdown bold syntax: **text** (two asterisks on both sides).

{recommendations_section}

## 6. SENTIMENT NARRATIVE (40-60 words)
Describe the emotional journey of the discussion:
- How did sentiment evolve across questions?
- Were there polarizing topics?
- What drove positive vs. negative reactions?

---

**IMPORTANT:**
- Use specific quotes and data points as evidence
- Avoid generic marketing jargon
- Be honest about weaknesses or concerns raised
- Consider both explicit feedback and implicit patterns
- Format using Markdown for readability (## headings, **bold** emphasis)
"""


RECOMMENDATIONS_SECTION_TEMPLATE = """
## 5. STRATEGIC RECOMMENDATIONS (2-3 bullet points, ≤25 words each)
Give the most valuable next steps for the product/marketing team.
Format every bullet as: **Actionable theme**: succinct action with expected impact.
Use proper markdown bold syntax: **text** (two asterisks on both sides).
Tie each recommendation to evidence from the discussion.
"""


DEMOGRAPHIC_CONTEXT_TEMPLATE = """
**PARTICIPANT DEMOGRAPHICS:**
- Sample size: {sample_size}
- Age range: {age_range}
- Gender distribution: {gender_distribution}
- Education levels: {education_levels}
"""


def build_discussion_summary_prompt(
    topic: str,
    description: str,
    discussion_text: str,
    demographic_summary: dict = None,
    include_recommendations: bool = True
) -> str:
    """
    Helper do budowania prompta dla podsumowania dyskusji.

    Args:
        topic: Temat grupy fokusowej
        description: Opis projektu
        discussion_text: Sformatowana transkrypcja dyskusji
        demographic_summary: Statystyki demograficzne (opcjonalne)
        include_recommendations: Czy zawrzeć sekcję rekomendacji

    Returns:
        Pełny prompt
    """
    # Format demographic context
    demo_context = ""
    if demographic_summary:
        # Format education levels (max 5)
        education_levels = demographic_summary.get('education_levels', [])
        education_str = ', '.join(education_levels[:5])

        demo_context = DEMOGRAPHIC_CONTEXT_TEMPLATE.format(
            sample_size=demographic_summary['sample_size'],
            age_range=demographic_summary['age_range'],
            gender_distribution=demographic_summary['gender_distribution'],
            education_levels=education_str
        )

    # Recommendations section
    recommendations_section = RECOMMENDATIONS_SECTION_TEMPLATE if include_recommendations else ""

    return DISCUSSION_SUMMARY_PROMPT_TEMPLATE.format(
        topic=topic,
        description=description or "No description provided",
        demo_context=demo_context,
        discussion_text=discussion_text,
        recommendations_section=recommendations_section
    )
