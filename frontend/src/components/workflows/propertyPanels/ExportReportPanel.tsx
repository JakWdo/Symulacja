/**
 * ExportReportPanel - Property panel dla EXPORT_REPORT node
 *
 * Generuje PDF/DOCX/JSON/CSV report z wyników workflow.
 * Config: report_name, format, sections, include_raw_data
 */

import { useState } from 'react';
import { Node } from 'reactflow';
import { ExportReportNodeConfig } from '@/types/workflowNodeConfigs';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { FileText, CheckSquare } from 'lucide-react';

interface ExportReportPanelProps {
  node: Node;
  onUpdate: (config: ExportReportNodeConfig) => void;
}

export function ExportReportPanel({ node, onUpdate }: ExportReportPanelProps) {
  const [config, setConfig] = useState<ExportReportNodeConfig>(
    (node.data.config as ExportReportNodeConfig) || {
      report_name: 'Research Report',
      format: 'pdf',
      sections: ['personas', 'survey_results', 'focus_group_summary'],
      include_raw_data: false,
    }
  );

  const handleChange = (field: keyof ExportReportNodeConfig, value: any) => {
    const updated = { ...config, [field]: value };
    setConfig(updated);
    onUpdate(updated);
  };

  const toggleSection = (section: string) => {
    const current = config.sections || [];
    const updated = current.includes(section)
      ? current.filter((s) => s !== section)
      : [...current, section];
    handleChange('sections', updated);
  };

  const availableSections = [
    { value: 'executive_summary', label: 'Executive Summary', description: 'High-level overview' },
    { value: 'personas', label: 'Personas', description: 'Profil wygenerowanych person' },
    { value: 'survey_results', label: 'Survey Results', description: 'Wyniki ankiety z wykresami' },
    { value: 'focus_group_summary', label: 'Focus Group Summary', description: 'Podsumowanie dyskusji' },
    { value: 'analysis', label: 'Analysis', description: 'AI analysis i insights' },
    { value: 'methodology', label: 'Methodology', description: 'Opis metodyki badania' },
    { value: 'recommendations', label: 'Recommendations', description: 'Rekomendacje biznesowe' },
  ];

  const formatDescriptions = {
    pdf: 'Profesjonalny PDF report z formatowaniem',
    docx: 'Edytowalny dokument Word',
    json: 'Surowe dane JSON (dla integracji)',
    csv: 'Dane tabelaryczne CSV',
  };

  return (
    <div className="space-y-4">
      {/* Report Name */}
      <div>
        <Label htmlFor="report-name">
          Report Name <span className="text-red-500">*</span>
        </Label>
        <Input
          id="report-name"
          value={config.report_name}
          onChange={(e) => handleChange('report_name', e.target.value)}
          className="mt-1.5"
          placeholder="e.g., Mobile App Research Report Q1 2025"
          required
        />
      </div>

      {/* Format */}
      <div>
        <Label htmlFor="format">
          Format <span className="text-red-500">*</span>
        </Label>
        <Select
          value={config.format}
          onValueChange={(v) =>
            handleChange('format', v as 'pdf' | 'docx' | 'json' | 'csv')
          }
        >
          <SelectTrigger id="format" className="mt-1.5">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="pdf">
              <div>
                <div className="font-medium flex items-center gap-2">
                  <FileText className="w-3.5 h-3.5" />
                  PDF
                </div>
                <div className="text-xs text-muted-foreground">
                  {formatDescriptions.pdf}
                </div>
              </div>
            </SelectItem>
            <SelectItem value="docx">
              <div>
                <div className="font-medium">DOCX</div>
                <div className="text-xs text-muted-foreground">
                  {formatDescriptions.docx}
                </div>
              </div>
            </SelectItem>
            <SelectItem value="json">
              <div>
                <div className="font-medium">JSON</div>
                <div className="text-xs text-muted-foreground">
                  {formatDescriptions.json}
                </div>
              </div>
            </SelectItem>
            <SelectItem value="csv">
              <div>
                <div className="font-medium">CSV</div>
                <div className="text-xs text-muted-foreground">
                  {formatDescriptions.csv}
                </div>
              </div>
            </SelectItem>
          </SelectContent>
        </Select>
        <p className="text-xs text-muted-foreground mt-1.5">
          {formatDescriptions[config.format]}
        </p>
      </div>

      {/* Sections (only for PDF/DOCX) */}
      {(config.format === 'pdf' || config.format === 'docx') && (
        <div>
          <Label className="mb-3 block">
            Report Sections <span className="text-red-500">*</span>
          </Label>
          <div className="space-y-2">
            {availableSections.map((section) => (
              <div
                key={section.value}
                className="flex items-start space-x-3 p-3 rounded-figma-inner border border-border hover:bg-muted/50 transition-colors"
              >
                <Checkbox
                  id={section.value}
                  checked={config.sections?.includes(section.value) || false}
                  onCheckedChange={() => toggleSection(section.value)}
                />
                <div className="flex-1">
                  <Label
                    htmlFor={section.value}
                    className="cursor-pointer font-medium"
                  >
                    {section.label}
                  </Label>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {section.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
          <div className="flex items-center gap-2 mt-2">
            <CheckSquare className="w-4 h-4 text-muted-foreground" />
            <p className="text-xs text-muted-foreground">
              Wybrano: {config.sections?.length || 0} sekcji
            </p>
          </div>
        </div>
      )}

      {/* Include Raw Data */}
      <div className="flex items-start space-x-3 p-3 rounded-figma-inner border border-border bg-muted/30">
        <Checkbox
          id="include-raw"
          checked={config.include_raw_data || false}
          onCheckedChange={(checked) => handleChange('include_raw_data', checked)}
        />
        <div className="flex-1">
          <Label htmlFor="include-raw" className="cursor-pointer font-medium">
            Include Raw Data (Appendix)
          </Label>
          <p className="text-xs text-muted-foreground mt-0.5">
            Dołącz surowe dane w appendixie raportu (zwiększa rozmiar pliku)
          </p>
        </div>
      </div>

      {/* Tier Info */}
      <div className="rounded-figma-inner border border-blue-200 bg-blue-50/50 p-4">
        <p className="text-xs text-blue-700">
          <strong>Tier Limits:</strong>
          <br />• Free: PDF z watermarkiem
          <br />• Pro: PDF/DOCX bez watermarku
          <br />• Enterprise: White-label exports + wszystkie formaty
        </p>
      </div>

      {/* File Size Estimate */}
      {config.format === 'pdf' || config.format === 'docx' ? (
        <div className="rounded-figma-inner border border-border bg-muted/30 p-3">
          <p className="text-xs font-medium mb-1">Estimated File Size:</p>
          <p className="text-xs text-muted-foreground">
            {config.sections.length * 0.5 + (config.include_raw_data ? 2 : 0)} MB
            - {config.sections.length * 1.5 + (config.include_raw_data ? 5 : 0)}{' '}
            MB
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            (zależnie od ilości danych w workflow)
          </p>
        </div>
      ) : (
        <div className="rounded-figma-inner border border-border bg-muted/30 p-3">
          <p className="text-xs font-medium mb-1">
            {config.format.toUpperCase()} Export:
          </p>
          <p className="text-xs text-muted-foreground">
            {config.format === 'json'
              ? 'Wszystkie dane workflow w formacie JSON'
              : 'Tabelaryczne dane eksportowane jako CSV'}
          </p>
        </div>
      )}
    </div>
  );
}
