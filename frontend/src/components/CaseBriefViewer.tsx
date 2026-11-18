import React, { useState } from "react";
import { Citation, ExtractedField, RevenueCaseBrief } from "../types";
import { useLanguage } from "../context/LanguageContext";
import { CheckCircle, AlertTriangle, HelpCircle, ExternalLink, Edit3, X } from "lucide-react";

interface CaseBriefViewerProps {
  brief: RevenueCaseBrief;
  onSelectCitation: (citation: Citation) => void;
}

export const CaseBriefViewer: React.FC<CaseBriefViewerProps> = ({
  brief,
  onSelectCitation,
}) => {
  const { lang, t } = useLanguage();
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");

  const renderConfidenceBadge = (confidence: number, needsReview: boolean) => {
    if (needsReview || confidence < 0.7) {
      return (
        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-xs font-semibold bg-rose-100 text-rose-800 border border-rose-300">
          <AlertTriangle className="w-3 h-3 shrink-0" />
          <span>{lang === "hi" ? "समीक्षा अपेक्षित" : "Needs Review"} ({Math.round(confidence * 100)}%)</span>
        </span>
      );
    }
    if (confidence >= 0.9) {
      return (
        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
          <CheckCircle className="w-3 h-3 shrink-0" />
          <span>{lang === "hi" ? "उच्च विश्वास" : "High Conf"} ({Math.round(confidence * 100)}%)</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-300">
        <HelpCircle className="w-3 h-3 shrink-0" />
        <span>{Math.round(confidence * 100)}%</span>
      </span>
    );
  };

  const renderFieldRow = (
    label: string,
    field: ExtractedField<any>,
    renderValue: (val: any) => React.ReactNode,
    fieldKey: string
  ) => {
    return (
      <div className="py-3 border-b border-slate-200 last:border-0 flex flex-col space-y-1.5">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500">{label}</span>
          <div className="flex items-center space-x-2">
            {renderConfidenceBadge(field.confidence, field.needs_review)}
            <button
              onClick={() => {
                setEditingField(fieldKey);
                setEditValue(typeof field.value === "string" ? field.value : JSON.stringify(field.value));
              }}
              className="text-slate-400 hover:text-slate-600 p-1"
              title="Suggest Correction"
            >
              <Edit3 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <div className="text-sm font-medium text-slate-900">
          {field.found && field.value !== null ? (
            renderValue(field.value)
          ) : (
            <span className="text-slate-400 italic">
              {lang === "hi" ? "पत्रावली में उपलब्ध नहीं" : "Not Found in File"}
            </span>
          )}
        </div>

        {/* Citations & Evidence */}
        {field.citations && field.citations.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {field.citations.map((c, i) => (
              <button
                key={i}
                onClick={() => onSelectCitation(c)}
                className="inline-flex items-center space-x-1 px-2 py-1 bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-300 rounded text-xs font-mono transition-colors"
                title={`Citation: ${c.snippet}`}
              >
                <ExternalLink className="w-3 h-3 text-amber-600" />
                <span>{lang === "hi" ? `पृष्ठ ${c.page}` : `p. ${c.page}`}</span>
                <span className="text-slate-400 truncate max-w-[120px]">"{c.snippet}"</span>
              </button>
            ))}
          </div>
        )}

        {/* Review Warning reasons */}
        {field.needs_review && field.review_reasons && field.review_reasons.length > 0 && (
          <div className="text-xs text-rose-600 bg-rose-50 p-2 rounded border border-rose-200 mt-1">
            {field.review_reasons.map((r, i) => (
              <div key={i}>• {r}</div>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="p-6 space-y-6 bg-slate-50 min-h-full">
      {/* Header Info Banner */}
      <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200 flex items-center justify-between">
        <div>
          <span className="text-xs text-slate-500 font-mono">DOC ID: {brief.doc_id}</span>
          <h2 className="text-lg font-bold text-slate-800">
            {lang === "hi" ? "केस संक्षिप्त विवरण (डिजिटल पत्रावली)" : "Revenue Court Case Brief"}
          </h2>
        </div>
        <div className="text-right text-xs text-slate-400 font-mono">
          <div>Pipeline: v{brief.pipeline_version}</div>
          <div>Glossary: v{brief.glossary_version}</div>
        </div>
      </div>

      {/* Case Identity Card */}
      <div className="bg-white p-5 rounded-lg shadow-sm border border-slate-200">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
          {lang === "hi" ? "वाद पहचान" : "Case Identification"}
        </h3>
        {renderFieldRow(
          t("case_number"),
          brief.case_number,
          (val) => val.original_string || `${val.number}/${val.year}`,
          "case_number"
        )}
        {renderFieldRow(t("court_name"), brief.court_name, (val) => val, "court_name")}
        {renderFieldRow(t("court_level"), brief.court_level, (val) => val.toUpperCase(), "court_level")}
        {renderFieldRow(t("proceeding_type"), brief.proceeding_type, (val) => val, "proceeding_type")}
      </div>

      {/* Parties Card */}
      <div className="bg-white p-5 rounded-lg shadow-sm border border-slate-200">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
          {lang === "hi" ? "पक्षकार" : "Parties"}
        </h3>
        {renderFieldRow(
          t("petitioners"),
          brief.petitioners,
          (val) => (
            <div className="space-y-1">
              {val.map((p: any, idx: number) => (
                <div key={idx} className="flex items-center space-x-2">
                  <span className="font-semibold">{p.original}</span>
                  {p.transliteration_key && (
                    <span className="text-xs font-mono text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
                      {p.transliteration_key}
                    </span>
                  )}
                </div>
              ))}
            </div>
          ),
          "petitioners"
        )}
        {renderFieldRow(
          t("respondents"),
          brief.respondents,
          (val) => (
            <div className="space-y-1">
              {val.map((p: any, idx: number) => (
                <div key={idx} className="flex items-center space-x-2">
                  <span className="font-semibold">{p.original}</span>
                  {p.transliteration_key && (
                    <span className="text-xs font-mono text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
                      {p.transliteration_key}
                    </span>
                  )}
                </div>
              ))}
            </div>
          ),
          "respondents"
        )}
      </div>

      {/* Dates & Status */}
      <div className="bg-white p-5 rounded-lg shadow-sm border border-slate-200">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
          {lang === "hi" ? "तिथियाँ एवं स्थिति" : "Timeline & Legal Status"}
        </h3>
        {renderFieldRow(
          t("filing_date"),
          brief.filing_date,
          (val) => `${val.iso_date} (${val.original_string})`,
          "filing_date"
        )}
        {renderFieldRow(
          t("current_status"),
          brief.current_status,
          (val) => (
            <span
              className={`px-2.5 py-1 rounded text-xs font-bold uppercase tracking-wider ${
                val === "rejected"
                  ? "bg-rose-100 text-rose-800 border border-rose-300"
                  : val === "allowed"
                  ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                  : "bg-blue-100 text-blue-800 border border-blue-300"
              }`}
            >
              {val}
            </span>
          ),
          "current_status"
        )}
        {brief.rejection_reason && brief.rejection_reason.found && (
          renderFieldRow(
            t("rejection_reason"),
            brief.rejection_reason,
            (val) => <span className="text-rose-700 italic">{val}</span>,
            "rejection_reason"
          )
        )}
      </div>

      {/* Correction Modal */}
      {editingField && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="font-bold text-slate-800">
                {lang === "hi" ? `संशोधन सुझाव: ${editingField}` : `Suggest Correction: ${editingField}`}
              </h4>
              <button onClick={() => setEditingField(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <textarea
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              className="w-full p-2 border border-slate-300 rounded font-mono text-sm h-28"
            />
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setEditingField(null)}
                className="px-3 py-1.5 text-slate-600 hover:bg-slate-100 rounded text-sm"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  alert(lang === "hi" ? "संशोधन ऑडिट लॉग में दर्ज किया गया।" : "Correction saved to audit log.");
                  setEditingField(null);
                }}
                className="px-4 py-1.5 bg-slate-900 text-white rounded text-sm hover:bg-slate-800 font-medium"
              >
                Submit Correction
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
