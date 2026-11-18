import React, { useState, useEffect } from "react";
import Head from "next/head";
import { LanguageProvider, useLanguage } from "../context/LanguageContext";
import { DocumentViewer } from "../components/DocumentViewer";
import { CaseBriefViewer } from "../components/CaseBriefViewer";
import { RulesPanel } from "../components/RulesPanel";
import { ConflictPanel } from "../components/ConflictPanel";
import { QAPanel } from "../components/QAPanel";
import {
  uploadDocument,
  getJobStatus,
  getCaseBrief,
  getRulesReport,
  getConflictsReport,
} from "../lib/api";
import {
  Citation,
  ConflictReport,
  RevenueCaseBrief,
  RuleCheckResult,
} from "../types";
import {
  Upload,
  Globe,
  Scale,
  FileCheck2,
  AlertCircle,
  FileText,
  ShieldCheck,
  CheckCircle2,
} from "lucide-react";

const MainDashboard: React.FC = () => {
  const { lang, setLang, t } = useLanguage();

  // Upload and Job State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [docId, setDocId] = useState<string | null>(null);
  const [filename, setFilename] = useState<string>("document.pdf");
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState("");
  const [error, setError] = useState<string | null>(null);

  // Completed Data State
  const [brief, setBrief] = useState<RevenueCaseBrief | null>(null);
  const [rules, setRules] = useState<RuleCheckResult[]>([]);
  const [conflicts, setConflicts] = useState<ConflictReport | null>(null);

  // UI Interactive State
  const [activeTab, setActiveTab] = useState<"brief" | "rules" | "conflicts" | "qa">("brief");
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);

  // Poll Job Progress
  useEffect(() => {
    if (!jobId || brief) return;

    const interval = setInterval(async () => {
      try {
        const statusResp = await getJobStatus(jobId);
        setProgress(statusResp.progress);
        setCurrentStep(statusResp.current_step);

        if (statusResp.status === "completed") {
          clearInterval(interval);
          // Fetch all artifacts
          const fetchedBrief = await getCaseBrief(statusResp.doc_id);
          const fetchedRules = await getRulesReport(statusResp.doc_id);
          const fetchedConflicts = await getConflictsReport(statusResp.doc_id);

          setBrief(fetchedBrief);
          setRules(fetchedRules.rules_results);
          setConflicts(fetchedConflicts);
          setUploading(false);
        } else if (statusResp.status === "failed") {
          clearInterval(interval);
          setError(statusResp.error || "Processing failed");
          setUploading(false);
        }
      } catch (err: any) {
        clearInterval(interval);
        setError(err.message || "Failed to poll job status");
        setUploading(false);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [jobId, brief]);

  const handleFileUpload = async (file: File) => {
    setSelectedFile(file);
    setFilename(file.name);
    setUploading(true);
    setError(null);
    setProgress(5);
    setCurrentStep("Uploading file to court engine...");

    try {
      const resp = await uploadDocument(file);
      setJobId(resp.job_id);
      setDocId(resp.doc_id);
    } catch (err: any) {
      setError(err.message || "Upload failed");
      setUploading(false);
    }
  };

  const handleSelectCitation = (citation: Citation) => {
    setActiveCitation(citation);
    setCurrentPage(citation.page);
  };

  return (
    <div className="flex flex-col h-screen bg-slate-100 overflow-hidden">
      <Head>
        <title>{t("app_title")}</title>
      </Head>

      {/* Mandatory Legal Disclaimer Banner */}
      <div className="bg-amber-500 text-slate-950 px-4 py-1.5 text-xs font-bold text-center tracking-wide flex items-center justify-center space-x-2 shrink-0 shadow-sm">
        <Scale className="w-4 h-4 shrink-0" />
        <span>{t("disclaimer")}</span>
      </div>

      {/* Main App Navigation Bar */}
      <header className="bg-slate-900 text-white px-6 py-3 flex items-center justify-between border-b border-slate-800 shrink-0 shadow-md">
        <div className="flex items-center space-x-3">
          <div className="bg-amber-500 text-slate-950 p-1.5 rounded font-black text-sm tracking-wider">
            AGY-COURT
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-tight text-white">{t("app_title")}</h1>
            <p className="text-[11px] text-slate-400">
              {lang === "hi"
                ? "राजस्व न्यायालय पत्रावली विश्लेषक (जिला स्तर)"
                : "District Court Revenue Case Engine"}
            </p>
          </div>
        </div>

        {/* Language & Actions Toggle */}
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setLang(lang === "hi" ? "en" : "hi")}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700"
          >
            <Globe className="w-3.5 h-3.5 text-amber-400" />
            <span>{lang === "hi" ? "English UI" : "हिंदी इंटरफ़ेस"}</span>
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      {!brief ? (
        /* Upload & Processing View */
        <main className="flex-1 flex items-center justify-center p-6">
          <div className="max-w-xl w-full bg-white rounded-xl shadow-lg border border-slate-200 p-8 text-center space-y-6">
            <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto text-slate-700">
              <Upload className="w-8 h-8" />
            </div>

            <div>
              <h2 className="text-xl font-bold text-slate-800">{t("upload_case_file")}</h2>
              <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">{t("drag_drop_prompt")}</p>
            </div>

            {/* Dropzone input */}
            {!uploading ? (
              <label className="border-2 border-dashed border-slate-300 hover:border-slate-400 rounded-lg p-8 block cursor-pointer bg-slate-50 hover:bg-slate-100 transition-colors">
                <input
                  type="file"
                  accept="application/pdf"
                  className="hidden"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) handleFileUpload(file);
                  }}
                />
                <span className="text-sm font-semibold text-slate-700 block mb-1">
                  {t("browse_files")}
                </span>
                <span className="text-xs text-slate-400">PDF up to 50MB</span>
              </label>
            ) : (
              /* Progress Indicator */
              <div className="space-y-4 py-4">
                <div className="flex justify-between text-xs font-semibold text-slate-600">
                  <span className="truncate max-w-xs">{currentStep}</span>
                  <span>{progress}%</span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2.5 overflow-hidden">
                  <div
                    className="bg-slate-900 h-2.5 rounded-full transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <div className="flex items-center justify-center space-x-2 text-xs text-slate-500">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  <span>PII masking active &bull; India data sovereign</span>
                </div>
              </div>
            )}

            {error && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded text-xs text-rose-700 text-left flex items-start space-x-2">
                <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}
          </div>
        </main>
      ) : (
        /* 50/50 Split Screen Workspace */
        <main className="flex-1 flex overflow-hidden">
          {/* Left Pane (50%): Document Viewer */}
          <div className="w-1/2 h-full">
            <DocumentViewer
              filename={filename}
              currentPage={currentPage}
              totalPages={1}
              onPageChange={(p) => setCurrentPage(p)}
              activeCitation={activeCitation}
              pageContent={brief.case_number.citations[0]?.snippet || ""}
            />
          </div>

          {/* Right Pane (50%): Tabs & Analysis */}
          <div className="w-1/2 h-full flex flex-col bg-white border-l border-slate-200">
            {/* Tab Navigation */}
            <div className="flex border-b border-slate-200 bg-slate-100 shrink-0 text-xs font-bold">
              <button
                onClick={() => setActiveTab("brief")}
                className={`flex-1 py-3 px-4 text-center border-b-2 transition-colors ${
                  activeTab === "brief"
                    ? "border-slate-900 text-slate-900 bg-white"
                    : "border-transparent text-slate-500 hover:text-slate-800"
                }`}
              >
                {t("tab_brief")}
              </button>
              <button
                onClick={() => setActiveTab("rules")}
                className={`flex-1 py-3 px-4 text-center border-b-2 transition-colors ${
                  activeTab === "rules"
                    ? "border-slate-900 text-slate-900 bg-white"
                    : "border-transparent text-slate-500 hover:text-slate-800"
                }`}
              >
                {t("tab_rules")} ({rules.length})
              </button>
              <button
                onClick={() => setActiveTab("conflicts")}
                className={`flex-1 py-3 px-4 text-center border-b-2 transition-colors ${
                  activeTab === "conflicts"
                    ? "border-slate-900 text-slate-900 bg-white"
                    : "border-transparent text-slate-500 hover:text-slate-800"
                }`}
              >
                {t("tab_conflicts")} ({conflicts?.total_conflicts || 0})
              </button>
              <button
                onClick={() => setActiveTab("qa")}
                className={`flex-1 py-3 px-4 text-center border-b-2 transition-colors ${
                  activeTab === "qa"
                    ? "border-slate-900 text-slate-900 bg-white"
                    : "border-transparent text-slate-500 hover:text-slate-800"
                }`}
              >
                {t("tab_qa")}
              </button>
            </div>

            {/* Tab Panels */}
            <div className="flex-1 overflow-y-auto">
              {activeTab === "brief" && (
                <CaseBriefViewer brief={brief} onSelectCitation={handleSelectCitation} />
              )}
              {activeTab === "rules" && <RulesPanel rules={rules} />}
              {activeTab === "conflicts" && conflicts && (
                <ConflictPanel report={conflicts} onSelectCitation={handleSelectCitation} />
              )}
              {activeTab === "qa" && docId && (
                <QAPanel docId={docId} onSelectCitation={handleSelectCitation} />
              )}
            </div>
          </div>
        </main>
      )}
    </div>
  );
};

export default function Home() {
  return (
    <LanguageProvider>
      <MainDashboard />
    </LanguageProvider>
  );
}
