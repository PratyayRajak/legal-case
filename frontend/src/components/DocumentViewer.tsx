import React from "react";
import { Citation } from "../types";
import { useLanguage } from "../context/LanguageContext";
import { FileText, ArrowLeft, ArrowRight, Bookmark } from "lucide-react";

interface DocumentViewerProps {
  filename?: string;
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  activeCitation: Citation | null;
  pageContent?: string;
}

export const DocumentViewer: React.FC<DocumentViewerProps> = ({
  filename = "document.pdf",
  currentPage,
  totalPages,
  onPageChange,
  activeCitation,
  pageContent = "",
}) => {
  const { lang, t } = useLanguage();

  return (
    <div className="flex flex-col h-full bg-slate-900 border-r border-slate-700 text-slate-100">
      {/* Viewer Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-slate-800 border-b border-slate-700">
        <div className="flex items-center space-x-2 truncate">
          <FileText className="w-5 h-5 text-amber-400 shrink-0" />
          <span className="font-medium text-sm truncate">{filename}</span>
        </div>

        {/* Page Navigation */}
        <div className="flex items-center space-x-2 shrink-0">
          <button
            disabled={currentPage <= 1}
            onClick={() => onPageChange(currentPage - 1)}
            className="p-1 rounded hover:bg-slate-700 disabled:opacity-40 disabled:hover:bg-transparent"
            title="Previous Page"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <span className="text-xs font-mono text-slate-300">
            {lang === "hi" ? `पृष्ठ ${currentPage} / ${totalPages || 1}` : `Page ${currentPage} of ${totalPages || 1}`}
          </span>
          <button
            disabled={currentPage >= totalPages}
            onClick={() => onPageChange(currentPage + 1)}
            className="p-1 rounded hover:bg-slate-700 disabled:opacity-40 disabled:hover:bg-transparent"
            title="Next Page"
          >
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Active Citation Notification Banner */}
      {activeCitation && (
        <div className="bg-amber-950/80 border-b border-amber-600/60 px-4 py-2 flex items-start space-x-2 text-xs text-amber-200">
          <Bookmark className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-amber-300">
              {lang === "hi" ? `साक्ष्य उद्धरण (पृष्ठ ${activeCitation.page}):` : `Active Citation (Page ${activeCitation.page}):`}
            </span>
            <p className="mt-0.5 italic text-slate-200 bg-amber-900/40 p-1.5 rounded border border-amber-800/60">
              "{activeCitation.snippet}"
            </p>
          </div>
        </div>
      )}

      {/* Page Content / Text Canvas */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        <div className="max-w-2xl mx-auto bg-white text-slate-900 shadow-2xl rounded p-8 min-h-[600px] border border-slate-300">
          <div className="text-right text-xs text-slate-400 font-mono mb-4 border-b pb-2">
            PAGE {currentPage}
          </div>

          {activeCitation && activeCitation.page === currentPage && (
            <div className="mb-4 p-3 bg-amber-50 border-l-4 border-amber-500 rounded text-amber-950 text-sm font-medium">
              <span className="text-xs uppercase tracking-wider text-amber-700 block mb-1">
                Highlighted Source Evidence / चयनित साक्ष्य
              </span>
              "{activeCitation.snippet}"
            </div>
          )}

          <div className="whitespace-pre-wrap font-serif leading-relaxed text-sm text-slate-800">
            {pageContent || (
              <div className="text-center py-20 text-slate-400">
                {lang === "hi" ? "दस्तावेज़ पृष्ठ पाठ प्रदर्शित हो रहा है..." : "Viewing extracted document text..."}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
