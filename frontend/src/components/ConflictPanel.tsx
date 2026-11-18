import React from "react";
import { Citation, ConflictReport } from "../types";
import { useLanguage } from "../context/LanguageContext";
import { AlertOctagon, AlertTriangle, ArrowRightLeft, ExternalLink } from "lucide-react";

interface ConflictPanelProps {
  report: ConflictReport;
  onSelectCitation: (citation: Citation) => void;
}

export const ConflictPanel: React.FC<ConflictPanelProps> = ({
  report,
  onSelectCitation,
}) => {
  const { lang } = useLanguage();

  return (
    <div className="p-6 space-y-6 bg-slate-50 min-h-full">
      <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <ArrowRightLeft className="w-5 h-5 text-amber-600" />
            <h2 className="text-lg font-bold text-slate-800">
              {lang === "hi" ? "दस्तावेज़ों में परस्पर विरोधाभास रिपोर्ट" : "Cross-Document Conflict Report"}
            </h2>
          </div>
          <span
            className={`px-2.5 py-1 rounded text-xs font-bold uppercase ${
              report.has_blocking
                ? "bg-rose-100 text-rose-800 border border-rose-300"
                : "bg-amber-100 text-amber-800 border border-amber-300"
            }`}
          >
            {report.total_conflicts} {lang === "hi" ? "विसंगतियों की पहचान" : "Inconsistencies Flagged"}
          </span>
        </div>
        <p className="text-xs text-slate-500 mt-1">
          {lang === "hi"
            ? "पत्रावली में शामिल विभिन्न प्रपत्रों (याचिका, आदेश पत्रक, संलग्नक) के बीच पाए गए अंतर्विरोध।"
            : "Inconsistencies detected across different documents within the case file (petition vs orders vs annexures)."}
        </p>
      </div>

      {report.conflicts.length === 0 ? (
        <div className="bg-white p-8 rounded-lg border border-slate-200 text-center text-slate-400">
          {lang === "hi"
            ? "पत्रावली में कोई अंतर्विरोध या विसंगति नहीं पाई गई।"
            : "No cross-document conflicts or contradictions detected in this case file."}
        </div>
      ) : (
        <div className="space-y-4">
          {report.conflicts.map((item, idx) => (
            <div
              key={idx}
              className={`bg-white p-5 rounded-lg shadow-sm border ${
                item.severity === "blocking" ? "border-rose-300 ring-1 ring-rose-200" : "border-amber-200"
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="font-mono text-xs font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded">
                  {item.conflict_type.toUpperCase()}
                </span>
                <span
                  className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded text-xs font-bold ${
                    item.severity === "blocking"
                      ? "bg-rose-100 text-rose-800 border border-rose-300"
                      : "bg-amber-100 text-amber-800 border border-amber-300"
                  }`}
                >
                  {item.severity === "blocking" ? (
                    <AlertOctagon className="w-3.5 h-3.5" />
                  ) : (
                    <AlertTriangle className="w-3.5 h-3.5" />
                  )}
                  <span>{item.severity.toUpperCase()}</span>
                </span>
              </div>

              <p className="text-sm text-slate-800 font-medium mb-3">
                {lang === "hi" ? item.description_hi : item.description_en}
              </p>

              {/* Dual Evidence Side-by-Side Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                {/* Evidence A */}
                <div className="bg-slate-50 p-3 rounded border border-slate-200 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-slate-600">
                        {lang === "hi" ? `साक्ष्य A (पृष्ठ ${item.evidence_a.page})` : `Evidence A (Page ${item.evidence_a.page})`}
                      </span>
                      <button
                        onClick={() => onSelectCitation(item.evidence_a)}
                        className="text-amber-700 hover:text-amber-900 text-xs inline-flex items-center space-x-1 font-mono"
                      >
                        <ExternalLink className="w-3 h-3" />
                        <span>View</span>
                      </button>
                    </div>
                    <p className="text-xs text-slate-700 italic font-serif bg-white p-2 rounded border border-slate-200">
                      "{item.evidence_a.snippet}"
                    </p>
                  </div>
                </div>

                {/* Evidence B */}
                <div className="bg-slate-50 p-3 rounded border border-slate-200 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-slate-600">
                        {lang === "hi" ? `साक्ष्य B (पृष्ठ ${item.evidence_b.page})` : `Evidence B (Page ${item.evidence_b.page})`}
                      </span>
                      <button
                        onClick={() => onSelectCitation(item.evidence_b)}
                        className="text-amber-700 hover:text-amber-900 text-xs inline-flex items-center space-x-1 font-mono"
                      >
                        <ExternalLink className="w-3 h-3" />
                        <span>View</span>
                      </button>
                    </div>
                    <p className="text-xs text-slate-700 italic font-serif bg-white p-2 rounded border border-slate-200">
                      "{item.evidence_b.snippet}"
                    </p>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
