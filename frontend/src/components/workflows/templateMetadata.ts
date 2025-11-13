/**
 * Template Metadata - statyczne metadane dla workflow templates
 *
 * NOTE: Moved to constants/workflows.ts for better organization
 * Re-exported here for backward compatibility
 */

export type {
  TemplateCategory,
  TemplateMetadata,
  WorkflowTemplateCard,
} from '../../constants/workflows';

export {
  TEMPLATE_METADATA,
  getTemplateMetadata,
  CATEGORY_LABELS,
  WORKFLOW_TEMPLATES as workflowTemplates,
} from '../../constants/workflows';
