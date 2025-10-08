// AI Summary types from discussion_summarizer service
export interface AISummaryResponse {
  executive_summary: string;
  key_insights: string[];
  surprising_findings: string[];
  segment_analysis: Record<string, string>;
  recommendations: string[];
  sentiment_narrative: string;
  full_analysis: string;
  metadata: {
    focus_group_id: string;
    focus_group_name: string;
    generated_at: string;
    model_used: string;
    total_responses: number;
    total_participants: number;
    questions_asked: number;
  };
}
