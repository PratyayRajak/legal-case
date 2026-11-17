# Known Limitations

## Phase 1 (Current)

This is the skeleton phase. No actual document processing is implemented.
All pipeline nodes are stubs.

## Planned Limitations (all phases)

### Handwriting Recognition
Handwritten text in documents is not supported. Only printed text
(digital PDF or scanned printed pages) is processed.
If a page appears to be handwritten, it is flagged with `needs_review=True`.

### Rule Coverage
Rules are PLACEHOLDER until provided by a qualified Hindi legal expert.
Current rules cover: court hierarchy, limitation period, jurisdiction,
required documents, date consistency. Additional rules require expert input.

### Glossary Review Status
All concepts in `glossary/concepts.yaml` are PLACEHOLDER and marked with
`review.reviewed_by: null`. A qualified Hindi legal expert must review and
approve each concept before the system is used in real proceedings.

### Case Types Supported
- v1: Revenue cases, district court level.
- Other case types (civil, criminal, family) require configuration additions:
  field set, questions, glossary concepts, rules.

### Language Support
- Supported: Hindi (Devanagari), English, mixed Hindi+English documents.
- Not supported: Other Indian scripts (Tamil, Telugu, etc.),
  handwriting, audio, video.

### OCR Quality
- Degraded scans (poor lighting, distortion, low DPI) may have high error rates.
- OCR confidence is reported per page so users can identify low-quality pages.
- Minimum recommended scan quality: 300 DPI, good contrast.

### AI Limitations
- The system assists and never decides.
- Extraction accuracy depends on document quality and LLM performance.
- Always verify extracted fields against the source document.
- Confidence scores are calibrated but not perfect.
