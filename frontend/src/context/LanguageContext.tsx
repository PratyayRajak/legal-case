import React, { createContext, useContext, useState } from "react";

type UILang = "en" | "hi";

interface LanguageContextType {
  lang: UILang;
  setLang: (lang: UILang) => void;
  t: (key: string) => string;
}

const translations: Record<string, Record<UILang, string>> = {
  app_title: {
    en: "Bilingual Case-Brief & Rule-Check Engine for Indian Courts",
    hi: "भारतीय न्यायालयों हेतु द्विभाषी केस-संक्षेप एवं नियम-जांच इंजन",
  },
  disclaimer: {
    en: "AI-assisted summary. Verify against the source document.",
    hi: "एआई-सहायता प्राप्त सारांश। मूल दस्तावेज़ से सत्यापन करें।",
  },
  upload_case_file: {
    en: "Upload Court File (PDF)",
    hi: "न्यायालय पत्रावली अपलोड करें (पीडीएफ)",
  },
  drag_drop_prompt: {
    en: "Drag and drop scanned or digital case PDF (Hindi, English, or Mixed)",
    hi: "स्कैन अथवा डिजिटल केस पीडीएफ यहाँ खींचें (हिंदी, अंग्रेजी या मिश्रित)",
  },
  browse_files: {
    en: "Browse Files",
    hi: "फ़ाइल चुनें",
  },
  tab_brief: {
    en: "Case Brief",
    hi: "केस संक्षेप",
  },
  tab_rules: {
    en: "Rule Compliance",
    hi: "नियम अनुपालन",
  },
  tab_conflicts: {
    en: "Cross-Document Conflicts",
    hi: "दस्तावेज़ विरोधाभास",
  },
  tab_qa: {
    en: "Follow-up Q&A",
    hi: "पत्रावली प्रश्न-उत्तर",
  },
  case_number: {
    en: "Case Number",
    hi: "वाद संख्या",
  },
  court_name: {
    en: "Court Name",
    hi: "न्यायालय का नाम",
  },
  court_level: {
    en: "Court Level",
    hi: "न्यायालय स्तर",
  },
  case_type: {
    en: "Case Type",
    hi: "वाद का प्रकार",
  },
  proceeding_type: {
    en: "Proceeding Type",
    hi: "कार्यवाही का स्वरूप",
  },
  petitioners: {
    en: "Petitioner(s)",
    hi: "वादी / याचिकाकर्ता",
  },
  respondents: {
    en: "Respondent(s)",
    hi: "प्रतिवादी / विपक्षी",
  },
  filing_date: {
    en: "Filing Date",
    hi: "संस्थित / दाखिल तिथि",
  },
  current_status: {
    en: "Current Status",
    hi: "वर्तमान स्थिति",
  },
  rejection_reason: {
    en: "Rejection / Dismissal Reason",
    hi: "खारिज करने का कारण",
  },
  evidence_citation: {
    en: "Evidence Citation",
    hi: "साक्ष्य उद्धरण",
  },
  confidence: {
    en: "Confidence",
    hi: "विश्वसनीयता",
  },
  ask_prompt: {
    en: "Ask a question in Hindi or English (grounded only in this document)...",
    hi: "पत्रावली के आधार पर हिंदी या अंग्रेजी में प्रश्न पूछें...",
  },
  ask_button: {
    en: "Ask",
    hi: "पूछें",
  },
};

const LanguageContext = createContext<LanguageContextType>({
  lang: "hi",
  setLang: () => {},
  t: (key: string) => key,
});

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [lang, setLang] = useState<UILang>("hi");

  const t = (key: string): string => {
    if (translations[key] && translations[key][lang]) {
      return translations[key][lang];
    }
    return key;
  };

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => useContext(LanguageContext);
