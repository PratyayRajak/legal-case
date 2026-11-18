export type Language = "hi" | "en" | "mixed";

export interface Citation {
  doc_id: string;
  page: number;
  snippet: string;
  lang: string;
  bbox?: {
    x0: number;
    y0: number;
    x1: number;
    y1: number;
  };
}

export interface ExtractedField<T = any> {
  field: string;
  value: T | null;
  found: boolean;
  confidence: number;
  citations: Citation[];
  needs_review: boolean;
  review_reasons: string[];
}

export interface RevenueCaseBrief {
  doc_id: string;
  pipeline_version: string;
  glossary_version: string;
  rules_version: string;
  case_number: ExtractedField<{
    case_type: string;
    number: string;
    year: number;
    original_string: string;
  }>;
  court_name: ExtractedField<string>;
  court_level: ExtractedField<string>;
  case_type: ExtractedField<string>;
  proceeding_type: ExtractedField<string>;
  petitioners: ExtractedField<Array<{ original: string; script: string; transliteration_key: string }>>;
  respondents: ExtractedField<Array<{ original: string; script: string; transliteration_key: string }>>;
  advocates: ExtractedField<string[]>;
  filing_date: ExtractedField<{ iso_date: string; precision: string; original_string: string }>;
  previous_hearing_dates: ExtractedField<string[]>;
  next_hearing_date: ExtractedField<{ iso_date: string; precision: string; original_string: string }>;
  current_status: ExtractedField<string>;
  rejection_reason: ExtractedField<string>;
  orders_summary: ExtractedField<any[]>;
  prior_court_history: ExtractedField<any[]>;
  documents_list: ExtractedField<any[]>;
  disclaimer: string;
}

export interface RuleCheckResult {
  rule_id: string;
  rule_version: string;
  result: "pass" | "fail" | "cannot_evaluate";
  severity: "blocking" | "warning";
  message_hi: string;
  message_en: string;
  evidence_citations: Citation[];
  missing_fields: string[];
}

export interface ConflictItem {
  conflict_id: string;
  conflict_type: string;
  field_name: string;
  description_en: string;
  description_hi: string;
  evidence_a: Citation;
  evidence_b: Citation;
  severity: "blocking" | "warning" | "info";
}

export interface ConflictReport {
  doc_id: string;
  conflicts: ConflictItem[];
  total_conflicts: number;
  has_blocking: boolean;
}

export interface JobStatusResponse {
  job_id: string;
  doc_id: string;
  status: "queued" | "processing" | "completed" | "failed";
  progress: number;
  current_step: string;
  error?: string;
  disclaimer: string;
}
