/**
 * ExportButton - reużywalny przycisk eksportu do PDF/DOCX
 */
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from '@/components/ui/dropdown-menu';
import { Download, FileText, File, Loader2 } from 'lucide-react';
import { exportPersona, exportFocusGroup, exportSurvey, ExportFormat } from '@/lib/api';
import { toast } from 'sonner';

type ExportType = 'persona' | 'focus-group' | 'survey';

interface ExportButtonProps {
  type: ExportType;
  id: number;
  variant?: 'default' | 'outline' | 'ghost';
  size?: 'default' | 'sm' | 'lg' | 'icon';
  includeOptions?: boolean; // Dla persony: includeReasoning, dla focus group: includeDiscussion
}

export function ExportButton({
  type,
  id,
  variant = 'outline',
  size = 'default',
  includeOptions = true,
}: ExportButtonProps) {
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async (format: ExportFormat) => {
    setIsExporting(true);

    try {
      switch (type) {
        case 'persona':
          await exportPersona(id, format, includeOptions);
          break;
        case 'focus-group':
          await exportFocusGroup(id, format, includeOptions);
          break;
        case 'survey':
          await exportSurvey(id, format);
          break;
      }

      toast.success(`Raport ${format.toUpperCase()} został pobrany`);
    } catch (error) {
      console.error('Export error:', error);
      toast.error(`Błąd podczas eksportu: ${error instanceof Error ? error.message : 'Nieznany błąd'}`);
    } finally {
      setIsExporting(false);
    }
  };

  const getLabel = () => {
    switch (type) {
      case 'persona':
        return 'Eksportuj personę';
      case 'focus-group':
        return 'Eksportuj grupę';
      case 'survey':
        return 'Eksportuj ankietę';
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant={variant} size={size} disabled={isExporting}>
          {isExporting ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Download className="w-4 h-4" />
          )}
          {size !== 'icon' && <span className="ml-2">{getLabel()}</span>}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-48">
        <DropdownMenuLabel>Format eksportu</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => handleExport('pdf')} disabled={isExporting}>
          <FileText className="w-4 h-4 mr-2" />
          Pobierz PDF
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleExport('docx')} disabled={isExporting}>
          <File className="w-4 h-4 mr-2" />
          Pobierz DOCX
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
