"""
Prompty dla grup fokusowych, ankiet i podsumowań dyskusji

Ten moduł zawiera wszystkie prompty związane z:
- Symulacjami grup fokusowych (FocusGroupServiceLangChain)
- Podsumowaniami dyskusji (DiscussionSummarizerService)
- Odpowiedziami na ankiety (SurveyResponseGenerator)
"""

from typing import Any, Dict, List
from langchain_core.prompts import ChatPromptTemplate


# ============================================================================
# 1. DISCUSSION SUMMARIZER - AI-powered podsumowania grup fokusowych
# ============================================================================

DISCUSSION_SUMMARIZER_SYSTEM_PROMPT = """You are a world-class market research analyst specializing in qualitative research synthesis.
Your role is to analyze focus group discussions and generate strategic insights for product teams.

IMPORTANT GUIDELINES:
- Be concise yet comprehensive
- Focus on actionable insights, not just description
- Identify patterns, contradictions, and surprising findings
- Consider demographic differences in opinions
- Provide strategic recommendations grounded in data
- Use professional, business-oriented language
- Avoid generic statements - be specific and evidence-based"""

DISCUSSION_SUMMARIZER_CHAT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", DISCUSSION_SUMMARIZER_SYSTEM_PROMPT),
    ("user", "{prompt}")
])


def create_summary_prompt(
    discussion_data: Dict[str, Any],
    include_recommendations: bool
) -> str:
    """
    Tworzy szczegółowy prompt do podsumowania AI dla focus group.

    Args:
        discussion_data: Dane dyskusji (topic, responses_by_question, demographic_summary)
        include_recommendations: Czy zawrzeć rekomendacje strategiczne

    Returns:
        Pełny prompt string z instrukcjami dla LLM
    """
    topic = discussion_data["topic"]
    description = discussion_data["description"] or "No description provided"
    responses_by_question = discussion_data["responses_by_question"]
    demo_summary = discussion_data.get("demographic_summary")

    # Formatujemy pytania wraz z odpowiedziami
    formatted_discussion = []
    for idx, (question, responses) in enumerate(responses_by_question.items(), 1):
        formatted_discussion.append(f"\n**Question {idx}:** {question}")
        formatted_discussion.append(f"*({len(responses)} responses)*\n")

        for ridx, resp in enumerate(responses[:15], 1):  # Ograniczamy do 15 dla tokenów
            text = resp["response"][:300]  # Skracamy bardzo długie wypowiedzi
            sentiment = resp["sentiment"]
            sentiment_label = "positive" if sentiment > 0.15 else "negative" if sentiment < -0.15 else "neutral"

            demo_str = ""
            if "demographics" in resp:
                demo = resp["demographics"]
                demo_str = f" ({demo['gender']}, {demo['age']}, {demo['occupation']})"

            formatted_discussion.append(
                f"{ridx}. [{sentiment_label.upper()}]{demo_str} \"{text}\""
            )

    discussion_text = "\n".join(formatted_discussion)

    # Kontekst demograficzny
    demo_context = ""
    if demo_summary:
        demo_context = f"""
**PARTICIPANT DEMOGRAPHICS:**
- Sample size: {demo_summary['sample_size']}
- Age range: {demo_summary['age_range']}
- Gender distribution: {demo_summary['gender_distribution']}
- Education levels: {', '.join(demo_summary['education_levels'][:5])}
"""

    recommendations_section = ""
    if include_recommendations:
        recommendations_section = """
## 5. STRATEGIC RECOMMENDATIONS (2-3 bullet points, ≤25 words each)
Give the most valuable next steps for the product/marketing team.
Format every bullet as: **Actionable theme**: succinct action with expected impact.
Use proper markdown bold syntax: **text** (two asterisks on both sides).
Tie each recommendation to evidence from the discussion.
"""

    prompt = f"""Analyze this focus group discussion and generate a comprehensive strategic summary.

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

    return prompt


# ============================================================================
# 2. FOCUS GROUP PERSONA RESPONSES - Symulacje odpowiedzi person
# ============================================================================

def create_focus_group_response_prompt(
    persona,
    question: str,
    context: List[Dict[str, Any]]
) -> str:
    """
    Utwórz prompt dla generowania odpowiedzi persony w focus group.

    Args:
        persona: Obiekt persony z pełnymi danymi
        question: Pytanie do odpowiedzi
        context: Lista poprzednich interakcji (z event sourcing)

    Returns:
        Pełny prompt gotowy do wysłania do LLM
    """

    # Formatuj kontekst poprzednich odpowiedzi (maksymalnie 3 najbardziej istotne)
    context_text = ""
    if context:
        context_text = "\n\nPast interactions:\n"
        for i, ctx in enumerate(context[:3], 1):  # Ograniczamy do 3 najważniejszych wpisów
            if ctx["event_type"] == "response_given":
                context_text += f"{i}. Q: {ctx['event_data'].get('question', '')}\n"
                context_text += f"   A: {ctx['event_data'].get('response', '')}\n"

    # Używamy pełnej historii tła persony
    background = persona.background_story if persona.background_story else 'Has diverse life experiences'

    return f"""You are participating in a focus group discussion.

PERSONA DETAILS:
Name: {persona.full_name or 'Participant'}
Age: {persona.age}, Gender: {persona.gender}
Occupation: {persona.occupation or 'Professional'}
Education: {persona.education_level or 'Educated'}
Location: {persona.location or 'Urban area'}

PERSONALITY:
Values: {', '.join(persona.values[:4]) if persona.values else 'Balanced approach to life'}
Interests: {', '.join(persona.interests[:4]) if persona.interests else 'Various interests'}

BACKGROUND:
{background}
{context_text}

QUESTION: {question}

Respond naturally as this person would in 2-4 sentences. Be authentic and conversational."""


# ============================================================================
# 3. SURVEY RESPONSES - Prompty dla różnych typów pytań ankietowych
# ============================================================================

SURVEY_SINGLE_CHOICE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are answering a survey question as a specific persona. Choose ONE option that best matches this persona's likely response. Return ONLY the chosen option text, nothing else."),
    ("user", """Persona Profile:
{persona_context}

Question: {question}
{description}

Options:
{options}

Choose the ONE option this persona would most likely select:""")
])


SURVEY_MULTIPLE_CHOICE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are answering a survey question as a specific persona. Choose one or MORE options that match this persona's likely response. Return ONLY a comma-separated list of chosen options, nothing else."),
    ("user", """Persona Profile:
{persona_context}

Question: {question}
{description}

Options:
{options}

Choose the options this persona would select (comma-separated):""")
])


SURVEY_RATING_SCALE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are answering a survey question as a specific persona. Provide a rating on a scale from {scale_min} to {scale_max}. Return ONLY the number, nothing else."),
    ("user", """Persona Profile:
{persona_context}

Question: {question}
{description}

Rate from {scale_min} (lowest) to {scale_max} (highest):""")
])


SURVEY_OPEN_TEXT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are answering a survey question as a specific persona. Provide a realistic, authentic response (2-4 sentences) that reflects this persona's perspective. Be concise and natural."),
    ("user", """Persona Profile:
{persona_context}

Question: {question}
{description}

Your response:""")
])


# ============================================================================
# Helper function for building persona context (used by all survey prompts)
# ============================================================================

def build_persona_context(persona) -> str:
    """
    Zbuduj kontekst persony dla promptu ankietowego.

    Args:
        persona: Obiekt Persona

    Returns:
        Sformatowany string z kontekstem persony
    """
    return f"""
Age: {persona.age}, Gender: {persona.gender}
Education: {persona.education_level or 'N/A'}
Income: {persona.income_bracket or 'N/A'}
Occupation: {persona.occupation or 'N/A'}
Location: {persona.location or 'N/A'}
Values: {', '.join(persona.values) if persona.values else 'N/A'}
Interests: {', '.join(persona.interests) if persona.interests else 'N/A'}
Background: {persona.background_story or 'N/A'}
""".strip()


# ============================================================================
# Survey helper functions for invoking prompts
# ============================================================================

def format_survey_options(options: List[str]) -> str:
    """Format survey options for display in prompt."""
    return chr(10).join(f'- {opt}' for opt in options)


def format_survey_description(description: str) -> str:
    """Format description field if present."""
    return f'Description: {description}' if description else ''
