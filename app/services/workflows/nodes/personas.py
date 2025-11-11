"""Executor dla node typu 'generate-personas'.

Integracja z PersonaOrchestrationService dla generacji person w ramach workflow.
"""

import logging
from typing import Any

from sqlalchemy import select

from app.models import Project
from app.schemas.workflow import GeneratePersonasNodeConfig
from app.services.personas import PersonaOrchestrationService
from app.services.workflows.nodes.base import NodeExecutor

logger = logging.getLogger(__name__)


class GeneratePersonasExecutor(NodeExecutor):
    """Executor dla generacji person w workflow.

    Używa PersonaOrchestrationService do tworzenia allocation plan,
    a następnie PersonaGeneratorLangChain do generacji konkretnych person.

    Flow:
    1. Pobierz project z demographic targets
    2. Stwórz allocation plan (orchestration)
    3. Generuj persony per grupa demograficzna (parallel)
    4. Zapisz persony do DB
    5. Zwróć persona_ids jako result
    """

    async def execute(
        self,
        node: dict,
        execution_context: dict[str, Any]
    ) -> dict[str, Any]:
        """Generuje persony używając PersonaOrchestration + PersonaGenerator.

        Args:
            node: Node config z {data: {config: {count, demographic_preset, ...}}}
            execution_context: Kontekst workflow

        Returns:
            {
                'persona_ids': [UUID, UUID, ...],
                'count': int,
                'demographics': {...},
                'groups': [{group_name, count, demographics}]
            }
        """
        # Parse config
        config_data = node.get('data', {}).get('config', {})
        config = GeneratePersonasNodeConfig(**config_data)

        project_id = execution_context['project_id']

        logger.info(
            f"Generating {config.count} personas for project {project_id} "
            f"(workflow node {node['id']})"
        )

        # 1. Load project z demographic targets
        stmt = select(Project).where(Project.id == project_id)
        result = await self.db.execute(stmt)
        project = result.scalar_one_or_none()

        if not project:
            raise ValueError(f"Project {project_id} not found")

        # 2. Przygotuj target demographics z config
        target_demographics = self._prepare_target_demographics(
            config, project
        )

        # 3. Stwórz allocation plan używając orchestration
        orchestrator = PersonaOrchestrationService()

        allocation_plan = await orchestrator.create_persona_allocation_plan(
            target_demographics=target_demographics,
            num_personas=config.count,
            project_description=config.project_description,
            additional_context=config.target_audience_description,
        )

        logger.info(
            f"Allocation plan created: {len(allocation_plan.groups)} groups"
        )

        # 4. Generuj persony per grupa using PersonaGeneratorLangChain
        # generator = PersonaGeneratorLangChain()  # Unused in MVP stub
        all_persona_ids = []

        for idx, group in enumerate(allocation_plan.groups):
            logger.info(
                f"Generating {group.count} personas for group {idx+1}: "
                f"{group.demographics}"
            )

            # TODO: Integrate with actual segment-based generation
            # Obecnie PersonaGenerator używa generate_persona_from_segment()
            # która wymaga segment_id, segment_name, segment_context
            #
            # Temporary solution: Generate personas poprzez bezpośrednie wywołanie LLM
            # z demographic constraints z grupy
            #
            # PRODUCTION TODO:
            # 1. Stwórz SegmentDefinition objects z allocation_plan.groups
            # 2. Zapisz segmenty do DB (jeśli potrzebne)
            # 3. Użyj generator.generate_persona_from_segment() dla każdej persony
            # 4. Zapisz persony do DB z proper relationships

            # STUB: Placeholder response (MVP - focus on workflow orchestration first)
            logger.warning(
                f"STUB: Persona generation for group {idx+1} not fully integrated yet. "
                "Using placeholder persona IDs."
            )

            # Generate placeholder persona IDs (w production będą to prawdziwe UUID z DB)
            from uuid import uuid4
            placeholder_ids = [str(uuid4()) for _ in range(group.count)]
            all_persona_ids.extend(placeholder_ids)

            logger.info(
                f"Generated {len(placeholder_ids)} placeholder personas for group"
            )

        persona_ids = all_persona_ids

        logger.info(
            f"Successfully generated {len(all_persona_ids)} personas "
            f"(workflow node {node['id']})"
        )

        # 6. Zwróć result
        return {
            'persona_ids': persona_ids,
            'count': len(all_persona_ids),
            'demographics': target_demographics,
            'groups': [
                {
                    'count': group.count,
                    'demographics': group.demographics,
                    'brief': group.brief[:200] + '...',  # Truncate for storage
                }
                for group in allocation_plan.groups
            ]
        }

    def _prepare_target_demographics(
        self,
        config: GeneratePersonasNodeConfig,
        project: Project
    ) -> dict[str, Any]:
        """Przygotuj target demographics z config + project.

        Priority:
        1. Config.advanced_options (jeśli podane)
        2. Config.demographic_preset (jeśli podany)
        3. Project.target_demographics (fallback)

        Args:
            config: Node config
            project: Project object z target_demographics

        Returns:
            Target demographics dict dla orchestration
        """
        # Start z project target demographics jako fallback
        target_demographics = project.target_demographics or {}

        # Override z demographic_preset (jeśli podany)
        if config.demographic_preset:
            # Load preset z config/demographics/
            # TODO: Implement preset loading (na razie use project demographics)
            logger.warning(
                f"Demographic preset '{config.demographic_preset}' "
                "not implemented yet, using project demographics"
            )

        # Override z advanced_options (jeśli podane)
        if config.advanced_options:
            target_demographics.update(config.advanced_options)

        return target_demographics
