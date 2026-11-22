export type RootCauseCandidate = {
  id: string;
  investigation_id: string;
  incident_id: string;
  service_id: string | null;
  deployment_id: string | null;
  cause_type: string;
  title: string;
  explanation: string;
  confidence_score: number;
  ranking: number;
  evidence_summary: {
    items?: Array<Record<string, unknown>>;
    score_note?: string;
    score_breakdown?: Record<string, unknown>;
  };
  supporting_evidence_count: number;
  contradicting_evidence_count: number;
  created_at: string;
  updated_at: string;
};

export type RootCauseListResponse = {
  investigation_id: string | null;
  version: number | null;
  status: string | null;
  items: RootCauseCandidate[];
  score_note: string;
};

export type RCAInvestigateResponse = {
  status: string;
  message: string;
  investigation_id: string | null;
  version: number;
  candidate_count: number;
  top_candidate_title: string | null;
  top_confidence_score: number;
};

export type InvestigationReportResponse = {
  report: Record<string, unknown>;
  markdown: string;
};