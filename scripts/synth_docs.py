"""Synthetic court PDF and ground-truth label generator.

Generates:
1. Pure Hindi documents (Devanagari, revenue cases).
2. Pure English documents (matching counterpart for cross-language consistency).
3. Mixed Hindi + English documents.
4. Digital PDFs and simulated scanned pages (good and degraded quality).
5. Ground truth labels in eval/data/labels/<doc_id>.json.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import cv2
import fitz  # PyMuPDF
import numpy as np


def find_devanagari_font() -> str | None:
    """Find an available font file supporting Devanagari."""
    candidates = [
        "C:/Windows/Fonts/Nirmala.ttc",
        "C:/Windows/Fonts/mangal.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansDevanagari-Regular.otf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def degrade_page(page: fitz.Page, noise_level: float = 25.0) -> bytes:
    """Convert a digital PDF page to a simulated scanned/degraded image."""
    pix = page.get_pixmap(dpi=150)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.h, pix.w, pix.n))

    # Add Gaussian noise
    noise = np.random.normal(0, noise_level, img.shape).astype(np.int16)
    degraded = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    # Slight contrast reduction
    scaled: np.ndarray[Any, Any] = cv2.convertScaleAbs(degraded, alpha=0.9, beta=15)

    _, buf = cv2.imencode(".png", scaled)
    return buf.tobytes()


SYNTHETIC_DOCS: list[dict[str, Any]] = [
    {
        "doc_id": "REV_001_HI",
        "pair_id": "CASE_PAIR_001",
        "language": "hi",
        "scan_quality": "digital",
        "case_type": "revenue",
        "pages_text": [
            [
                "न्यायालय उप-जिलाधिकारी / परगनाधिकारी, सदर, जनपद लखनऊ",
                "वाद संख्या: 104 / 2024",
                "दायर करने की तिथि: 15/01/2024",
                "",
                "प्रकरण: नामांतरण (दाखिल खारिज)",
                "वादी: राम कुमार शर्मा, पुत्र स्व. श्याम सुंदर शर्मा, निवासी ग्राम बख्शी का तालाब, लखनऊ",
                "बनाम",
                "प्रतिवादी: मोहन लाल वर्मा, पुत्र किशोरी लाल, निवासी ग्राम बख्शी का तालाब, लखनऊ",
                "",
                "आदेश",
                "आज यह पत्रावली पेश हुई। उभय पक्षों के विद्वान अधिवक्ता उपस्थित हैं।",
                "वादी की ओर से प्रस्तुत नामांतरण प्रार्थना पत्र का परीक्षण किया गया।",
                "भूमि खसरा संख्या 452, रकबा 0.450 हेक्टेयर, ग्राम बख्शी का तालाब के संबंध में",
                "प्रतिवादी द्वारा प्रस्तुत आपत्ति एवं साक्ष्य का अवलोकन किया गया।",
                "वादी द्वारा आवश्यक राजस्व खतौनी एवं प्रमाणित प्रति प्रस्तुत नहीं की गई।",
                "अतः पत्रावली पर उपलब्ध साक्ष्यों के आधार पर यह आवेदन खारिज किया जाता है।",
                "",
                "तारीख: 15/01/2024",
                "हस्ताक्षर: उप-जिलाधिकारी, सदर",
            ]
        ],
        "label": {
            "doc_id": "REV_001_HI",
            "pair_id": "CASE_PAIR_001",
            "doc_language": "hi",
            "scan_quality": "digital",
            "case_type": "revenue",
            "fields": {
                "case_number": {
                    "found": True,
                    "value": {"case_type": "case", "number": "104", "year": 2024, "original_string": "104 / 2024"},
                    "page": 1,
                    "snippet": "वाद संख्या: 104 / 2024",
                },
                "court_name": {
                    "found": True,
                    "value": "उप-जिलाधिकारी सदर लखनऊ",
                    "page": 1,
                    "snippet": "न्यायालय उप-जिलाधिकारी / परगनाधिकारी, सदर, जनपद लखनऊ",
                },
                "court_level": {"found": True, "value": "district", "page": 1, "snippet": "जनपद लखनऊ"},
                "case_type": {"found": True, "value": "revenue", "page": 1, "snippet": "नामांतरण"},
                "proceeding_type": {"found": True, "value": "mutation", "page": 1, "snippet": "नामांतरण"},
                "petitioners": {
                    "found": True,
                    "value": [{"original": "राम कुमार शर्मा", "script": "devanagari", "transliteration_key": "ram_kumar_sarma"}],
                    "page": 1,
                    "snippet": "वादी: राम कुमार शर्मा",
                },
                "respondents": {
                    "found": True,
                    "value": [{"original": "मोहन लाल वर्मा", "script": "devanagari", "transliteration_key": "mohan_lal_varma"}],
                    "page": 1,
                    "snippet": "प्रतिवादी: मोहन लाल वर्मा",
                },
                "filing_date": {
                    "found": True,
                    "value": {"iso_date": "2024-01-15", "precision": "full", "original_string": "15/01/2024"},
                    "page": 1,
                    "snippet": "दायर करने की तिथि: 15/01/2024",
                },
                "next_hearing_date": {"found": False, "value": None},
                "current_status": {"found": True, "value": "rejected", "page": 1, "snippet": "आवेदन खारिज किया जाता है।"},
                "rejection_reason": {
                    "found": True,
                    "value": "वादी द्वारा आवश्यक राजस्व खतौनी एवं प्रमाणित प्रति प्रस्तुत नहीं की गई।",
                    "page": 1,
                    "snippet": "वादी द्वारा आवश्यक राजस्व खतौनी एवं प्रमाणित प्रति प्रस्तुत नहीं की गई।",
                },
            },
            "rule_expectations": {
                "R001_PLACEHOLDER": "cannot_evaluate",
                "R002_PLACEHOLDER": "pass",
                "R003_PLACEHOLDER": "pass",
                "R004_PLACEHOLDER": "cannot_evaluate",
                "R005_PLACEHOLDER": "cannot_evaluate",
            },
        },
    },
    {
        "doc_id": "REV_001_EN",
        "pair_id": "CASE_PAIR_001",
        "language": "en",
        "scan_quality": "digital",
        "case_type": "revenue",
        "pages_text": [
            [
                "Court of Sub-Divisional Magistrate / S.D.M. Sadar, District Lucknow",
                "Case No.: 104 / 2024",
                "Date of Filing: 15/01/2024",
                "",
                "Matter: Mutation of Land Records",
                "Petitioner: Ram Kumar Sharma, s/o Late Shyam Sunder Sharma, r/o Bakshi Ka Talab, Lucknow",
                "Versus",
                "Respondent: Mohan Lal Verma, s/o Kishori Lal, r/o Bakshi Ka Talab, Lucknow",
                "",
                "Order",
                "The file was presented today. Learned counsels for both parties appeared.",
                "The application for mutation submitted by the petitioner has been examined.",
                "Regarding Khasra No. 452, Area 0.450 Hectare, Village Bakshi Ka Talab,",
                "objections and evidence submitted by respondent have been perused.",
                "The petitioner failed to produce certified copies of revenue records (khatauni).",
                "Therefore, in light of available evidence, this petition is hereby dismissed.",
                "",
                "Date: 15/01/2024",
                "Signed: Sub-Divisional Magistrate, Sadar",
            ]
        ],
        "label": {
            "doc_id": "REV_001_EN",
            "pair_id": "CASE_PAIR_001",
            "doc_language": "en",
            "scan_quality": "digital",
            "case_type": "revenue",
            "fields": {
                "case_number": {
                    "found": True,
                    "value": {"case_type": "case", "number": "104", "year": 2024, "original_string": "104 / 2024"},
                    "page": 1,
                    "snippet": "Case No.: 104 / 2024",
                },
                "court_name": {
                    "found": True,
                    "value": "SDM Sadar District Lucknow",
                    "page": 1,
                    "snippet": "Court of Sub-Divisional Magistrate / S.D.M. Sadar, District Lucknow",
                },
                "court_level": {"found": True, "value": "district", "page": 1, "snippet": "District Lucknow"},
                "case_type": {"found": True, "value": "revenue", "page": 1, "snippet": "Mutation of Land Records"},
                "proceeding_type": {"found": True, "value": "mutation", "page": 1, "snippet": "Mutation of Land Records"},
                "petitioners": {
                    "found": True,
                    "value": [{"original": "Ram Kumar Sharma", "script": "latin", "transliteration_key": "ram_kumar_sarma"}],
                    "page": 1,
                    "snippet": "Petitioner: Ram Kumar Sharma",
                },
                "respondents": {
                    "found": True,
                    "value": [{"original": "Mohan Lal Verma", "script": "latin", "transliteration_key": "mohan_lal_varma"}],
                    "page": 1,
                    "snippet": "Respondent: Mohan Lal Verma",
                },
                "filing_date": {
                    "found": True,
                    "value": {"iso_date": "2024-01-15", "precision": "full", "original_string": "15/01/2024"},
                    "page": 1,
                    "snippet": "Date of Filing: 15/01/2024",
                },
                "next_hearing_date": {"found": False, "value": None},
                "current_status": {"found": True, "value": "rejected", "page": 1, "snippet": "this petition is hereby dismissed."},
                "rejection_reason": {
                    "found": True,
                    "value": "The petitioner failed to produce certified copies of revenue records (khatauni).",
                    "page": 1,
                    "snippet": "The petitioner failed to produce certified copies of revenue records (khatauni).",
                },
            },
            "rule_expectations": {
                "R001_PLACEHOLDER": "cannot_evaluate",
                "R002_PLACEHOLDER": "pass",
                "R003_PLACEHOLDER": "pass",
                "R004_PLACEHOLDER": "cannot_evaluate",
                "R005_PLACEHOLDER": "cannot_evaluate",
            },
        },
    },
    {
        "doc_id": "REV_002_MIXED",
        "pair_id": "CASE_PAIR_002",
        "language": "mixed",
        "scan_quality": "digital",
        "case_type": "revenue",
        "pages_text": [
            [
                "BEFORE THE SUB-DIVISIONAL OFFICER, TEHSIL MOHANLALGANJ",
                "Case No.: 215/2023",
                "Filing Date: 10-09-2023",
                "Subject: Partition Suit under Section 116 Revenue Code (बँटवारा वाद)",
                "",
                "Applicant: Suresh Chandra Pandey (सुरेश चंद्र पांडे)",
                "Versus",
                "Opposite Party: Ramesh Chandra Pandey (रमेश चंद्र पांडे)",
                "",
                "Order Sheet / आदेश पत्रक",
                "दिनांक: 12-04-2024",
                "पत्रावली प्रस्तुत। पक्षकारों के अधिवक्तागण हाजिर आए।",
                "लेखपाल / पटवारी आख्या संलग्न पत्रावली की गई।",
                "अगली सुनवाई हेतु पत्रावली दिनांक 25-05-2024 को पेश हो।",
                "Next Date of Hearing: 25-05-2024",
                "Status: Pending / विचाराधीन",
            ]
        ],
        "label": {
            "doc_id": "REV_002_MIXED",
            "pair_id": "CASE_PAIR_002",
            "doc_language": "mixed",
            "scan_quality": "digital",
            "case_type": "revenue",
            "fields": {
                "case_number": {
                    "found": True,
                    "value": {"case_type": "case", "number": "215", "year": 2023, "original_string": "215/2023"},
                    "page": 1,
                    "snippet": "Case No.: 215/2023",
                },
                "court_name": {"found": True, "value": "SDO Mohanlalganj", "page": 1, "snippet": "SUB-DIVISIONAL OFFICER, TEHSIL MOHANLALGANJ"},
                "court_level": {"found": True, "value": "district", "page": 1, "snippet": "TEHSIL MOHANLALGANJ"},
                "case_type": {"found": True, "value": "revenue", "page": 1, "snippet": "Section 116 Revenue Code"},
                "proceeding_type": {"found": True, "value": "partition", "page": 1, "snippet": "Partition Suit"},
                "petitioners": {
                    "found": True,
                    "value": [{"original": "Suresh Chandra Pandey", "script": "latin", "transliteration_key": "sures_candra_pandey"}],
                    "page": 1,
                    "snippet": "Applicant: Suresh Chandra Pandey",
                },
                "respondents": {
                    "found": True,
                    "value": [{"original": "Ramesh Chandra Pandey", "script": "latin", "transliteration_key": "rames_candra_pandey"}],
                    "page": 1,
                    "snippet": "Opposite Party: Ramesh Chandra Pandey",
                },
                "filing_date": {
                    "found": True,
                    "value": {"iso_date": "2023-09-10", "precision": "full", "original_string": "10-09-2023"},
                    "page": 1,
                    "snippet": "Filing Date: 10-09-2023",
                },
                "next_hearing_date": {
                    "found": True,
                    "value": {"iso_date": "2024-05-25", "precision": "full", "original_string": "25-05-2024"},
                    "page": 1,
                    "snippet": "Next Date of Hearing: 25-05-2024",
                },
                "current_status": {"found": True, "value": "pending", "page": 1, "snippet": "Status: Pending / विचाराधीन"},
                "rejection_reason": {"found": False, "value": None},
            },
            "rule_expectations": {
                "R001_PLACEHOLDER": "cannot_evaluate",
                "R002_PLACEHOLDER": "pass",
                "R003_PLACEHOLDER": "pass",
                "R004_PLACEHOLDER": "cannot_evaluate",
                "R005_PLACEHOLDER": "pass",
            },
        },
    },
    {
        "doc_id": "REV_003_SCAN_GOOD",
        "pair_id": "CASE_PAIR_003",
        "language": "hi",
        "scan_quality": "good",
        "case_type": "revenue",
        "pages_text": [
            [
                "न्यायालय तहसीलदार, सदर, वाराणसी",
                "वाद सं.: 312 / 2023",
                "दाखिल तिथि: 12-08-2023",
                "प्रकरण: सीमांकन एवं सीमा विवाद (खसरा सं. 89)",
                "वादी: केदारनाथ यादव",
                "प्रतिवादी: शिवबालक यादव",
                "आदेश: पत्रावली विचाराधीन है। आगामी सुनवाई 10-06-2024 को नियत की जाती है।",
            ]
        ],
        "label": {
            "doc_id": "REV_003_SCAN_GOOD",
            "pair_id": "CASE_PAIR_003",
            "doc_language": "hi",
            "scan_quality": "good",
            "case_type": "revenue",
            "fields": {
                "case_number": {
                    "found": True,
                    "value": {"case_type": "case", "number": "312", "year": 2023, "original_string": "312 / 2023"},
                    "page": 1,
                    "snippet": "वाद सं.: 312 / 2023",
                },
                "court_name": {"found": True, "value": "तहसीलदार सदर वाराणसी", "page": 1, "snippet": "न्यायालय तहसीलदार, सदर, वाराणसी"},
                "court_level": {"found": True, "value": "district", "page": 1, "snippet": "वाराणसी"},
                "case_type": {"found": True, "value": "revenue", "page": 1, "snippet": "सीमांकन एवं सीमा विवाद"},
                "proceeding_type": {"found": True, "value": "boundary_dispute", "page": 1, "snippet": "सीमा विवाद"},
                "petitioners": {
                    "found": True,
                    "value": [{"original": "केदारनाथ यादव", "script": "devanagari", "transliteration_key": "kedarnath_yadav"}],
                    "page": 1,
                    "snippet": "वादी: केदारनाथ यादव",
                },
                "respondents": {
                    "found": True,
                    "value": [{"original": "शिवबालक यादव", "script": "devanagari", "transliteration_key": "sivabalak_yadav"}],
                    "page": 1,
                    "snippet": "प्रतिवादी: शिवबालक यादव",
                },
                "filing_date": {
                    "found": True,
                    "value": {"iso_date": "2023-08-12", "precision": "full", "original_string": "12-08-2023"},
                    "page": 1,
                    "snippet": "दाखिल तिथि: 12-08-2023",
                },
                "next_hearing_date": {
                    "found": True,
                    "value": {"iso_date": "2024-06-10", "precision": "full", "original_string": "10-06-2024"},
                    "page": 1,
                    "snippet": "आगामी सुनवाई 10-06-2024 को नियत की जाती है।",
                },
                "current_status": {"found": True, "value": "pending", "page": 1, "snippet": "पत्रावली विचाराधीन है।"},
                "rejection_reason": {"found": False, "value": None},
            },
            "rule_expectations": {
                "R001_PLACEHOLDER": "cannot_evaluate",
                "R002_PLACEHOLDER": "pass",
                "R003_PLACEHOLDER": "pass",
                "R004_PLACEHOLDER": "cannot_evaluate",
                "R005_PLACEHOLDER": "pass",
            },
        },
    },
    {
        "doc_id": "REV_004_SCAN_POOR",
        "pair_id": "CASE_PAIR_004",
        "language": "hi",
        "scan_quality": "poor",
        "case_type": "revenue",
        "pages_text": [
            [
                "न्यायालय अपर जिलाधिकारी (वित्त एवं राजस्व), गोरखपुर",
                "अपील संख्या: 55/2022",
                "दाखिल तिथि: 04-03-2022",
                "प्रकरण: राजस्व अपील विरुद्ध आदेश तहसीलदार",
                "अपीलार्थी: जगदीश प्रसाद मिश्र",
                "प्रत्यर्थी: राज्य उत्तर प्रदेश एवं अन्य",
                "आदेश: अपील स्वीकार की जाती है। अवर न्यायालय का आदेश निरस्त किया जाता है।",
            ]
        ],
        "label": {
            "doc_id": "REV_004_SCAN_POOR",
            "pair_id": "CASE_PAIR_004",
            "doc_language": "hi",
            "scan_quality": "poor",
            "case_type": "revenue",
            "fields": {
                "case_number": {
                    "found": True,
                    "value": {"case_type": "appeal", "number": "55", "year": 2022, "original_string": "55/2022"},
                    "page": 1,
                    "snippet": "अपील संख्या: 55/2022",
                },
                "court_name": {"found": True, "value": "ADM गोरखपुर", "page": 1, "snippet": "न्यायालय अपर जिलाधिकारी"},
                "court_level": {"found": True, "value": "district", "page": 1, "snippet": "गोरखपुर"},
                "case_type": {"found": True, "value": "revenue", "page": 1, "snippet": "राजस्व अपील"},
                "proceeding_type": {"found": True, "value": "other", "page": 1, "snippet": "राजस्व अपील"},
                "petitioners": {
                    "found": True,
                    "value": [{"original": "जगदीश प्रसाद मिश्र", "script": "devanagari", "transliteration_key": "jagdis_prasad_misra"}],
                    "page": 1,
                    "snippet": "अपीलार्थी: जगदीश प्रसाद मिश्र",
                },
                "respondents": {
                    "found": True,
                    "value": [{"original": "राज्य उत्तर प्रदेश", "script": "devanagari", "transliteration_key": "rajya_uttar_prades"}],
                    "page": 1,
                    "snippet": "प्रत्यर्थी: राज्य उत्तर प्रदेश",
                },
                "filing_date": {
                    "found": True,
                    "value": {"iso_date": "2022-03-04", "precision": "full", "original_string": "04-03-2022"},
                    "page": 1,
                    "snippet": "दाखिल तिथि: 04-03-2022",
                },
                "next_hearing_date": {"found": False, "value": None},
                "current_status": {"found": True, "value": "allowed", "page": 1, "snippet": "अपील स्वीकार की जाती है।"},
                "rejection_reason": {"found": False, "value": None},
            },
            "rule_expectations": {
                "R001_PLACEHOLDER": "cannot_evaluate",
                "R002_PLACEHOLDER": "pass",
                "R003_PLACEHOLDER": "pass",
                "R004_PLACEHOLDER": "cannot_evaluate",
                "R005_PLACEHOLDER": "cannot_evaluate",
            },
        },
    },
    {
        "doc_id": "REV_005_RULE_INCONSISTENT",
        "pair_id": "CASE_PAIR_005",
        "language": "en",
        "scan_quality": "digital",
        "case_type": "revenue",
        "pages_text": [
            [
                "IN THE COURT OF DISTRICT MAGISTRATE, PRAYAGRAJ",
                "Case No.: 999 / 2024",
                "Filing Date: 2024-06-01",
                "Next Hearing Date: 2024-01-10",
                "",
                "Matter: Land Acquisition Compensation",
                "Petitioner: Ankit Verma",
                "Respondent: State of UP",
                "Status: Pending",
            ]
        ],
        "label": {
            "doc_id": "REV_005_RULE_INCONSISTENT",
            "pair_id": "CASE_PAIR_005",
            "doc_language": "en",
            "scan_quality": "digital",
            "case_type": "revenue",
            "fields": {
                "case_number": {
                    "found": True,
                    "value": {"case_type": "case", "number": "999", "year": 2024, "original_string": "999 / 2024"},
                    "page": 1,
                    "snippet": "Case No.: 999 / 2024",
                },
                "court_name": {"found": True, "value": "DM Prayagraj", "page": 1, "snippet": "DISTRICT MAGISTRATE, PRAYAGRAJ"},
                "court_level": {"found": True, "value": "district", "page": 1, "snippet": "PRAYAGRAJ"},
                "case_type": {"found": True, "value": "revenue", "page": 1, "snippet": "Land Acquisition"},
                "proceeding_type": {"found": True, "value": "land_acquisition", "page": 1, "snippet": "Land Acquisition"},
                "petitioners": {
                    "found": True,
                    "value": [{"original": "Ankit Verma", "script": "latin", "transliteration_key": "ankit_verma"}],
                    "page": 1,
                    "snippet": "Petitioner: Ankit Verma",
                },
                "respondents": {
                    "found": True,
                    "value": [{"original": "State of UP", "script": "latin", "transliteration_key": "state_of_up"}],
                    "page": 1,
                    "snippet": "Respondent: State of UP",
                },
                "filing_date": {
                    "found": True,
                    "value": {"iso_date": "2024-06-01", "precision": "full", "original_string": "2024-06-01"},
                    "page": 1,
                    "snippet": "Filing Date: 2024-06-01",
                },
                "next_hearing_date": {
                    "found": True,
                    "value": {"iso_date": "2024-01-10", "precision": "full", "original_string": "2024-01-10"},
                    "page": 1,
                    "snippet": "Next Hearing Date: 2024-01-10",
                },
                "current_status": {"found": True, "value": "pending", "page": 1, "snippet": "Status: Pending"},
                "rejection_reason": {"found": False, "value": None},
            },
            "rule_expectations": {
                "R001_PLACEHOLDER": "cannot_evaluate",
                "R002_PLACEHOLDER": "pass",
                "R003_PLACEHOLDER": "pass",
                "R004_PLACEHOLDER": "cannot_evaluate",
                "R005_PLACEHOLDER": "fail",  # Filing date (June 2024) is AFTER next hearing date (Jan 2024)
            },
        },
    },
]


def generate_synthetic_data(
    docs_dir: Path | str = "eval/data/docs",
    labels_dir: Path | str = "eval/data/labels",
) -> list[str]:
    """Generate synthetic PDF documents and corresponding ground-truth JSON labels."""
    docs_path = Path(docs_dir)
    labels_path = Path(labels_dir)
    docs_path.mkdir(parents=True, exist_ok=True)
    labels_path.mkdir(parents=True, exist_ok=True)

    font_path = find_devanagari_font()
    generated_ids: list[str] = []

    for item in SYNTHETIC_DOCS:
        doc_id = item["doc_id"]
        pdf_file = docs_path / f"{doc_id}.pdf"
        json_file = labels_path / f"{doc_id}.json"

        # Create temporary digital document first
        doc = fitz.open()
        for page_lines in item["pages_text"]:
            page = doc.new_page(width=595, height=842)
            fontname = "helv"
            if font_path and any(
                sum(1 for ch in line if "\u0900" <= ch <= "\u097F") > 0 for line in page_lines
            ):
                page.insert_font(fontname="dev_font", fontfile=font_path)
                fontname = "dev_font"

            y = 50
            for line in page_lines:
                if line:
                    page.insert_text(
                        (50, y),
                        line,
                        fontname=fontname,
                        fontsize=11 if y > 80 else 13,
                    )
                y += 22

        if item["scan_quality"] in ["good", "poor"]:
            # Convert each page to a degraded scanned image in a new document
            noise_level = 15.0 if item["scan_quality"] == "good" else 40.0
            doc_scanned = fitz.open()
            for p in doc:
                scanned_bytes = degrade_page(p, noise_level=noise_level)
                p_scan = doc_scanned.new_page(width=595, height=842)
                p_scan.insert_image(p_scan.rect, stream=scanned_bytes)
            doc_scanned.save(str(pdf_file))
            doc_scanned.close()
            doc.close()
        else:
            doc.save(str(pdf_file))
            doc.close()

        # Save label JSON
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(item["label"], f, ensure_ascii=False, indent=2)

        generated_ids.append(doc_id)

    return generated_ids


if __name__ == "__main__":
    ids = generate_synthetic_data()
    print(f"Generated {len(ids)} synthetic documents and labels: {ids}")
