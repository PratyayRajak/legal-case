"""Table extraction and Land Record (Khatauni / Khasra) structure parser.

Handles:
1. Gata / Khasra plot numbers (गाटा संख्या / खसरा नं)
2. Land area in Hectares (क्षेत्रफल हेक्टेयर)
3. Landholder / Co-sharer names (खातेदार का नाम)
4. Order / Mutation entries (आदेश / प्रविष्टि विवरण)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from eval.normalize import convert_hindi_digits_to_ascii


@dataclass
class LandRecordEntry:
    khasra_number: str
    area_hectares: float
    landholders: list[str] = field(default_factory=list)
    mutation_notes: str = ""


@dataclass
class LandTableExtractionResult:
    doc_id: str
    page_number: int
    total_plots: int
    entries: list[LandRecordEntry]
    raw_table_found: bool


class LandRecordTableParser:
    """Specialized structural parser for Indian Revenue Court Khatauni and Khasra tables."""

    # Plot number regex (e.g. गाटा सं. 124/2 or Khasra No. 45)
    PLOT_REGEX = re.compile(
        r"(?:गाटा\s*(?:संख्या|सं|नं)?\.?|खसरा\s*(?:संख्या|सं|नं)?\.?|khasra\s*no\.?|plot\s*no\.?)\s*[:\-]?\s*([०-९0-9]+(?:\/[०-९0-9]+)?)",
        re.IGNORECASE | re.UNICODE,
    )

    # Area regex (e.g. क्षेत्रफल 0.4500 हेक्टेयर or Area 1.250 Ha)
    AREA_REGEX = re.compile(
        r"(?:क्षेत्रफल|रकबा|area)\s*[:\-]?\s*([०-९0-9]+(?:\.[०-९0-9]+)?)\s*(?:हेक्टेयर|हे०|ha|hectare)?",
        re.IGNORECASE | re.UNICODE,
    )

    # Co-sharer / Landholder marker
    KHATEDAR_REGEX = re.compile(
        r"(?:खातेदार|काश्तकार|भूस्वामी|owner|landholder)\s*[:\-]?\s*([^\n\r,;।]+)",
        re.IGNORECASE | re.UNICODE,
    )

    def parse_page_table(self, page_text: str, doc_id: str = "doc", page_number: int = 1) -> LandTableExtractionResult:
        """Parse structured land records from page text."""
        normalized_text = convert_hindi_digits_to_ascii(page_text)
        entries: list[LandRecordEntry] = []

        # Find all plot numbers
        plot_matches = list(self.PLOT_REGEX.finditer(normalized_text))
        area_matches = list(self.AREA_REGEX.finditer(normalized_text))
        holder_matches = list(self.KHATEDAR_REGEX.finditer(normalized_text))

        has_table_markers = bool(plot_matches or area_matches or "खतौनी" in page_text or "खाता संख्या" in page_text)

        if plot_matches:
            for idx, p_match in enumerate(plot_matches):
                plot_no = p_match.group(1).strip()
                # Associate nearest area
                area_val = 0.0
                if idx < len(area_matches):
                    try:
                        area_val = float(area_matches[idx].group(1).strip())
                    except ValueError:
                        area_val = 0.0

                # Associate landholders
                holders: list[str] = []
                if idx < len(holder_matches):
                    h_name = holder_matches[idx].group(1).strip()
                    if len(h_name) > 2:
                        holders.append(h_name)

                entries.append(
                    LandRecordEntry(
                        khasra_number=plot_no,
                        area_hectares=area_val,
                        landholders=holders,
                        mutation_notes="नामान्तरण प्रविष्टि",
                    )
                )

        return LandTableExtractionResult(
            doc_id=doc_id,
            page_number=page_number,
            total_plots=len(entries),
            entries=entries,
            raw_table_found=has_table_markers,
        )
