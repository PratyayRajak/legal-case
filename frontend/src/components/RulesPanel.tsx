import React from "react";
import { RuleCheckResult } from "../types";
import { useLanguage } from "../context/LanguageContext";
import { CheckCircle2, XCircle, AlertCircle, ShieldAlert, BookOpen } from "lucide-react";

interface RulesPanelProps {
  rules: RuleCheckResult[];
}

export const RulesPanel: React.FC<RulesPanelProps> = ({ rules }) => {
  const { lang } = useLanguage();

  const renderResultBadge = (result: string) => {
    switch (result) {
      case "pass":
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 uppercase tracking-wide">
            <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
            <span>{lang === "hi" ? "अनुपालन (PASS)" : "COMPLIED (PASS)"}</span>
          </span>
        );
      case "fail":
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded text-xs font-bold bg-rose-100 text-rose-800 border border-rose-300 uppercase tracking-wide">
            <XCircle className="w-3.5 h-3.5 shrink-0" />
            <span>{lang === "hi" ? "उल्लंघन (FAIL)" : "VIOLATION (FAIL)"}</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded text-xs font-bold bg-slate-100 text-slate-700 border border-slate-300 uppercase tracking-wide">
            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
            <span>{lang === "hi" ? "मूल्यांकन संभव नहीं" : "CANNOT EVALUATE"}</span>
          </span>
        );
    }
  };

  return (
    <div className="p-6 space-y-6 bg-slate-50 min-h-full">
      <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <BookOpen className="w-5 h-5 text-indigo-700" />
            <h2 className="text-lg font-bold text-slate-800">
              {lang === "hi" ? "प्रक्रियात्मक नियम अनुपालन रिपोर्ट" : "Procedural Rule Compliance Report"}
            </h2>
          </div>
          <span className="text-xs font-mono text-slate-500">
            {rules.length} {lang === "hi" ? "नियम जाँचे गए" : "Rules Evaluated"}
          </span>
        </div>
        <p className="text-xs text-slate-500 mt-1">
          {lang === "hi"
            ? "नियमों का मूल्यांकन केवल निर्धारित कैनोनिकल फ़ील्ड्स पर किया गया है (अनुवादित पाठ पर कभी नहीं)।"
            : "Rules evaluated deterministically on canonical case fields only — never on raw translated text."}
        </p>
      </div>

      <div className="space-y-4">
        {rules.map((r, idx) => (
          <div
            key={idx}
            className={`bg-white p-5 rounded-lg shadow-sm border ${
              r.result === "fail"
                ? "border-rose-300 ring-1 ring-rose-200"
                : r.result === "pass"
                ? "border-emerald-200"
                : "border-slate-200"
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                  {r.rule_id}
                </span>
                {r.severity === "blocking" && (
                  <span className="inline-flex items-center space-x-1 text-xs font-bold text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
                    <ShieldAlert className="w-3 h-3" />
                    <span>BLOCKING</span>
                  </span>
                )}
              </div>
              {renderResultBadge(r.result)}
            </div>

            {/* Original Hindi legal text of record */}
            <div className="mt-3 bg-amber-50/70 p-3 rounded border border-amber-200/80">
              <span className="text-[10px] font-bold uppercase tracking-wider text-amber-800 block mb-1">
                Hindi Rule Text (Authority / मूल विधिक पाठ)
              </span>
              <p className="text-sm font-serif text-slate-900 leading-relaxed font-medium">
                {r.message_hi}
              </p>
            </div>

            {/* Explanation message in user's UI language */}
            <div className="mt-3 text-xs text-slate-600">
              <span className="font-semibold text-slate-700">Explanation: </span>
              {lang === "hi" ? r.message_hi : r.message_en}
            </div>

            {r.missing_fields && r.missing_fields.length > 0 && (
              <div className="mt-2 text-xs text-amber-800 bg-amber-50 p-2 rounded border border-amber-200">
                Missing / Unverified required fields: {r.missing_fields.join(", ")}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
