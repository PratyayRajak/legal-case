import {
  ConflictReport,
  JobStatusResponse,
  RevenueCaseBrief,
  RuleCheckResult,
} from "../types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

export async function uploadDocument(file: File): Promise<{
  doc_id: string;
  job_id: string;
  doc_hash: string;
  status: string;
  filename: string;
  disclaimer: string;
}> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/documents/upload`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(error.detail || "Failed to upload file");
  }

  return res.json();
}

export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch job status: ${res.statusText}`);
  }
  return res.json();
}

export async function getCaseBrief(docId: string): Promise<RevenueCaseBrief> {
  const res = await fetch(`${API_BASE}/documents/${docId}/brief`);
  if (!res.ok) {
    throw new Error(`Failed to fetch brief: ${res.statusText}`);
  }
  return res.json();
}

export async function getRulesReport(docId: string): Promise<{
  doc_id: string;
  rules_results: RuleCheckResult[];
  total_rules: number;
  disclaimer: string;
}> {
  const res = await fetch(`${API_BASE}/documents/${docId}/rules`);
  if (!res.ok) {
    throw new Error(`Failed to fetch rules: ${res.statusText}`);
  }
  return res.json();
}

export async function getConflictsReport(docId: string): Promise<ConflictReport> {
  const res = await fetch(`${API_BASE}/documents/${docId}/conflicts`);
  if (!res.ok) {
    throw new Error(`Failed to fetch conflicts: ${res.statusText}`);
  }
  return res.json();
}

export async function askQuestion(
  docId: string,
  question: string
): Promise<{
  doc_id: string;
  question: string;
  answer: string;
  citations: Array<{ page: number; snippet: string; lang: string }>;
  language: string;
  disclaimer: string;
}> {
  const res = await fetch(`${API_BASE}/qa/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_id: docId, question }),
  });

  if (!res.ok) {
    throw new Error(`Failed to ask question: ${res.statusText}`);
  }
  return res.json();
}

export function getDocumentPdfExportUrl(docId: string): string {
  return `${API_BASE}/documents/${docId}/export/pdf`;
}

export function getDocumentTextExportUrl(docId: string): string {
  return `${API_BASE}/documents/${docId}/export/text`;
}
