import React, { useState } from "react";
import { Citation } from "../types";
import { useLanguage } from "../context/LanguageContext";
import { askQuestion } from "../lib/api";
import { MessageSquare, Send, ExternalLink, ShieldCheck } from "lucide-react";

interface QAMessage {
  question: string;
  answer: string;
  citations: Array<{ page: number; snippet: string; lang: string }>;
  timestamp: string;
}

interface QAPanelProps {
  docId: string;
  onSelectCitation: (citation: Citation) => void;
}

export const QAPanel: React.FC<QAPanelProps> = ({ docId, onSelectCitation }) => {
  const { lang, t } = useLanguage();
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<QAMessage[]>([]);

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    const currentQ = query;
    setQuery("");
    setLoading(true);

    try {
      const resp = await askQuestion(docId, currentQ);
      setMessages((prev) => [
        ...prev,
        {
          question: currentQ,
          answer: resp.answer,
          citations: resp.citations,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          question: currentQ,
          answer: `Error: ${err.message || "Unable to get answer"}`,
          citations: [],
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-50">
      {/* Header */}
      <div className="bg-white p-4 border-b border-slate-200">
        <div className="flex items-center space-x-2">
          <MessageSquare className="w-5 h-5 text-indigo-700" />
          <h2 className="text-base font-bold text-slate-800">
            {lang === "hi" ? "दस्तावेज़-आधारित प्रश्न-उत्तर" : "File-Grounded Follow-up Q&A"}
          </h2>
        </div>
        <div className="flex items-center space-x-1.5 text-xs text-slate-500 mt-1">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
          <span>
            {lang === "hi"
              ? "उत्तर केवल संलग्न पत्रावली के आधार पर दिए जाते हैं।"
              : "Responses are grounded exclusively in this uploaded court file."}
          </span>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center py-16 text-slate-400 space-y-2">
            <MessageSquare className="w-8 h-8 mx-auto text-slate-300" />
            <p className="text-sm">
              {lang === "hi"
                ? "पत्रावली के विषय में कोई भी प्रश्न पूछें (उदा. 'आदेश की मुख्य बातें क्या हैं?')"
                : "Ask any question about this case (e.g., 'What were the grounds for rejection?')"}
            </p>
          </div>
        ) : (
          messages.map((m, idx) => (
            <div key={idx} className="space-y-2">
              {/* User Question */}
              <div className="flex justify-end">
                <div className="bg-slate-800 text-white p-3 rounded-lg max-w-lg text-sm shadow-sm">
                  {m.question}
                  <div className="text-[10px] text-slate-400 text-right mt-1 font-mono">{m.timestamp}</div>
                </div>
              </div>

              {/* System Answer */}
              <div className="flex justify-start">
                <div className="bg-white border border-slate-200 text-slate-900 p-4 rounded-lg max-w-xl text-sm shadow-sm space-y-2">
                  <p className="font-serif leading-relaxed">{m.answer}</p>

                  {/* Citations */}
                  {m.citations && m.citations.length > 0 && (
                    <div className="pt-2 border-t border-slate-100 flex flex-wrap gap-1.5">
                      {m.citations.map((c, i) => (
                        <button
                          key={i}
                          onClick={() =>
                            onSelectCitation({
                              doc_id: docId,
                              page: c.page,
                              snippet: c.snippet,
                              lang: c.lang || "hi",
                            })
                          }
                          className="inline-flex items-center space-x-1 px-2 py-0.5 bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-300 rounded text-xs font-mono"
                        >
                          <ExternalLink className="w-3 h-3 text-amber-600" />
                          <span>{lang === "hi" ? `पृष्ठ ${c.page}` : `p. ${c.page}`}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Input Form */}
      <form onSubmit={handleAsk} className="p-4 bg-white border-t border-slate-200 flex space-x-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t("ask_prompt")}
          className="flex-1 px-4 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600"
        />
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-sm font-semibold flex items-center space-x-1 disabled:opacity-40"
        >
          <Send className="w-4 h-4" />
          <span>{loading ? "..." : t("ask_button")}</span>
        </button>
      </form>
    </div>
  );
};
