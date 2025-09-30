from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from app.models import Persona
from app.services.persona_generator_langchain import PersonaGeneratorLangChain as PersonaGenerator, DemographicDistribution
from app.core.config import get_settings

settings = get_settings()


class AdversarialService:
    """
    Generate adversarial personas for campaign stress testing
    Creates edge cases, devil's advocates, and extreme profiles
    """

    def __init__(self):
        self.settings = settings
        self.persona_generator = PersonaGenerator()
        if settings.OPENAI_API_KEY:
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        if settings.ANTHROPIC_API_KEY:
            self.anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def generate_adversarial_personas(
        self,
        db: AsyncSession,
        project_id: str,
        campaign_description: str,
        target_distribution: DemographicDistribution,
        num_personas: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Generate adversarial personas designed to stress-test a campaign
        """

        adversarial_personas = []

        # Strategy 1: Extreme personalities (20% of personas)
        extreme_count = max(1, num_personas // 5)
        for _ in range(extreme_count):
            persona = await self._create_extreme_persona(
                project_id, campaign_description, target_distribution
            )
            adversarial_personas.append(persona)

        # Strategy 2: Devil's advocates (30% of personas)
        advocate_count = max(1, num_personas * 3 // 10)
        for _ in range(advocate_count):
            persona = await self._create_devils_advocate(
                project_id, campaign_description, target_distribution
            )
            adversarial_personas.append(persona)

        # Strategy 3: Edge demographic cases (20% of personas)
        edge_count = max(1, num_personas // 5)
        for _ in range(edge_count):
            persona = await self._create_edge_case_persona(
                project_id, campaign_description, target_distribution
            )
            adversarial_personas.append(persona)

        # Strategy 4: Contrarian personalities (30% of personas)
        contrarian_count = num_personas - (extreme_count + advocate_count + edge_count)
        for _ in range(contrarian_count):
            persona = await self._create_contrarian_persona(
                project_id, campaign_description, target_distribution
            )
            adversarial_personas.append(persona)

        return adversarial_personas[:num_personas]

    async def _create_extreme_persona(
        self,
        project_id: str,
        campaign_description: str,
        distribution: DemographicDistribution,
    ) -> Dict[str, Any]:
        """Create persona with extreme psychological traits"""

        # Sample demographics normally
        demographic = self.persona_generator.sample_demographic_profile(distribution)[0]

        # Create extreme psychological profile
        trait = np.random.choice([
            "openness", "conscientiousness", "extraversion",
            "agreeableness", "neuroticism"
        ])

        psychological_profile = self.persona_generator.sample_big_five_traits()
        # Push selected trait to extreme (0 or 1)
        psychological_profile[trait] = np.random.choice([0.05, 0.95])

        # Extreme cultural dimensions
        cultural = self.persona_generator.sample_cultural_dimensions()
        cultural_trait = np.random.choice(list(cultural.keys()))
        cultural[cultural_trait] = np.random.choice([0.05, 0.95])

        psychological_profile.update(cultural)

        # Generate personality with adversarial context
        prompt, personality = await self._generate_adversarial_personality(
            demographic, psychological_profile, campaign_description, "extreme"
        )

        return self._build_persona_dict(
            project_id, demographic, psychological_profile, prompt, personality
        )

    async def _create_devils_advocate(
        self,
        project_id: str,
        campaign_description: str,
        distribution: DemographicDistribution,
    ) -> Dict[str, Any]:
        """Create persona specifically designed to challenge campaign assumptions"""

        demographic = self.persona_generator.sample_demographic_profile(distribution)[0]
        psychological_profile = self.persona_generator.sample_big_five_traits()
        psychological_profile.update(self.persona_generator.sample_cultural_dimensions())

        # Generate personality with critical thinking emphasis
        prompt, personality = await self._generate_adversarial_personality(
            demographic, psychological_profile, campaign_description, "devils_advocate"
        )

        return self._build_persona_dict(
            project_id, demographic, psychological_profile, prompt, personality
        )

    async def _create_edge_case_persona(
        self,
        project_id: str,
        campaign_description: str,
        distribution: DemographicDistribution,
    ) -> Dict[str, Any]:
        """Create persona with unusual demographic combinations"""

        # Create unusual demographic combination
        demographic = self.persona_generator.sample_demographic_profile(distribution)[0]

        # Deliberately create mismatches (e.g., high education + low income)
        if np.random.random() > 0.5:
            demographic["education_level"] = list(distribution.education_levels.keys())[-1]
            demographic["income_bracket"] = list(distribution.income_brackets.keys())[0]
        else:
            demographic["education_level"] = list(distribution.education_levels.keys())[0]
            demographic["income_bracket"] = list(distribution.income_brackets.keys())[-1]

        psychological_profile = self.persona_generator.sample_big_five_traits()
        psychological_profile.update(self.persona_generator.sample_cultural_dimensions())

        prompt, personality = await self._generate_adversarial_personality(
            demographic, psychological_profile, campaign_description, "edge_case"
        )

        return self._build_persona_dict(
            project_id, demographic, psychological_profile, prompt, personality
        )

    async def _create_contrarian_persona(
        self,
        project_id: str,
        campaign_description: str,
        distribution: DemographicDistribution,
    ) -> Dict[str, Any]:
        """Create persona with contrarian tendencies"""

        demographic = self.persona_generator.sample_demographic_profile(distribution)[0]

        # Contrarian psychological profile
        psychological_profile = self.persona_generator.sample_big_five_traits()
        psychological_profile["agreeableness"] = np.clip(np.random.normal(0.3, 0.1), 0, 1)
        psychological_profile["openness"] = np.clip(np.random.normal(0.7, 0.1), 0, 1)

        cultural = self.persona_generator.sample_cultural_dimensions()
        cultural["individualism"] = np.clip(np.random.normal(0.7, 0.1), 0, 1)
        psychological_profile.update(cultural)

        prompt, personality = await self._generate_adversarial_personality(
            demographic, psychological_profile, campaign_description, "contrarian"
        )

        return self._build_persona_dict(
            project_id, demographic, psychological_profile, prompt, personality
        )

    async def _generate_adversarial_personality(
        self,
        demographic: Dict[str, Any],
        psychological: Dict[str, Any],
        campaign_description: str,
        adversarial_type: str,
    ) -> tuple[str, str]:
        """Generate adversarial personality using LLM"""

        type_instructions = {
            "extreme": "This persona has EXTREME personality traits. Make them intensely opinionated and uncompromising.",
            "devils_advocate": "This persona is a DEVIL'S ADVOCATE who naturally questions assumptions and finds flaws. They're intellectually critical and skeptical.",
            "edge_case": "This persona has an UNUSUAL life situation that creates unique perspectives. They don't fit typical patterns.",
            "contrarian": "This persona is CONTRARIAN by nature - they instinctively disagree with mainstream views and offer alternative perspectives.",
        }

        prompt = f"""Create a synthetic ADVERSARIAL persona for stress-testing this marketing campaign:

CAMPAIGN: {campaign_description}

PERSONA TYPE: {adversarial_type.upper()}
{type_instructions.get(adversarial_type, '')}

DEMOGRAPHICS:
- Age Group: {demographic.get('age_group')}
- Gender: {demographic.get('gender')}
- Education: {demographic.get('education_level')}
- Income: {demographic.get('income_bracket')}
- Location: {demographic.get('location')}

PSYCHOLOGICAL PROFILE (Big Five, 0-1 scale):
- Openness: {psychological.get('openness', 0.5):.2f}
- Conscientiousness: {psychological.get('conscientiousness', 0.5):.2f}
- Extraversion: {psychological.get('extraversion', 0.5):.2f}
- Agreeableness: {psychological.get('agreeableness', 0.5):.2f}
- Neuroticism: {psychological.get('neuroticism', 0.5):.2f}

Generate a JSON response with:
1. "background_story": A compelling 2-3 sentence background explaining their challenging perspective
2. "values": List of 5-7 values that might CONFLICT with typical marketing
3. "interests": List of 5-7 interests
4. "communication_style": How they express disagreement or skepticism
5. "decision_making_style": How they critically evaluate claims
6. "typical_concerns": Specific issues they would raise about marketing campaigns
7. "hot_buttons": Topics that trigger strong negative reactions

Make this persona realistic but challenging - they should stress-test campaign messaging."""

        if self.settings.DEFAULT_LLM_PROVIDER == "openai":
            response = await self._generate_with_openai(prompt)
        else:
            response = await self._generate_with_anthropic(prompt)

        return prompt, response

    async def _generate_with_openai(self, prompt: str) -> str:
        """Generate using OpenAI"""
        response = await self.openai_client.chat.completions.create(
            model=self.settings.DEFAULT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are creating adversarial personas for marketing stress testing. Always respond with valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=self.settings.TEMPERATURE,
            max_tokens=self.settings.MAX_TOKENS,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content

    async def _generate_with_anthropic(self, prompt: str) -> str:
        """Generate using Anthropic Claude"""
        response = await self.anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=self.settings.MAX_TOKENS,
            temperature=self.settings.TEMPERATURE,
            messages=[
                {
                    "role": "user",
                    "content": f"{prompt}\n\nRespond only with valid JSON, no other text.",
                }
            ],
        )
        return response.content[0].text

    def _build_persona_dict(
        self,
        project_id: str,
        demographic: Dict[str, Any],
        psychological: Dict[str, Any],
        prompt: str,
        personality_json: str,
    ) -> Dict[str, Any]:
        """Build persona dictionary from components"""
        import json

        personality = json.loads(personality_json)

        # Extract age from age group (take midpoint)
        age_group = demographic.get("age_group", "25-34")
        if "-" in age_group:
            age_parts = age_group.split("-")
            age = (int(age_parts[0]) + int(age_parts[1])) // 2
        else:
            age = 35  # default

        return {
            "project_id": project_id,
            "age": age,
            "gender": demographic.get("gender"),
            "location": demographic.get("location"),
            "education_level": demographic.get("education_level"),
            "income_bracket": demographic.get("income_bracket"),
            "occupation": personality.get("occupation", "N/A"),
            "openness": psychological.get("openness"),
            "conscientiousness": psychological.get("conscientiousness"),
            "extraversion": psychological.get("extraversion"),
            "agreeableness": psychological.get("agreeableness"),
            "neuroticism": psychological.get("neuroticism"),
            "power_distance": psychological.get("power_distance"),
            "individualism": psychological.get("individualism"),
            "masculinity": psychological.get("masculinity"),
            "uncertainty_avoidance": psychological.get("uncertainty_avoidance"),
            "long_term_orientation": psychological.get("long_term_orientation"),
            "indulgence": psychological.get("indulgence"),
            "values": personality.get("values", []),
            "interests": personality.get("interests", []),
            "background_story": personality.get("background_story", ""),
            "personality_prompt": prompt,
        }