# Figure 1 Architecture Scaffold

Status: scaffold only. Replace with a rendered figure after implementation is stable.

```mermaid
flowchart LR
    Input[Public image/volume data] --> Import[Import layer<br/>NIfTI, PNG, TIFF]
    Import --> GUI[Tkinter annotation GUI]
    Import --> Headless[Headless benchmark runner]
    GUI --> Manual[Manual polygon editing]
    GUI --> Router[Transparent agentic router]
    Headless --> Router
    Router --> Classical[Classical OpenCV<br/>watershed/levelset]
    Router --> Cellpose[Optional Cellpose backend]
    Router --> LangSAM[LangSAM bridge]
    Router --> MedSAM[MedSAM bridge]
    Router --> MedSAM2[MedSAM2 bridge]
    Manual --> Memory[Project/session memory<br/>prompts, bboxes, seeds]
    Router --> Memory
    Router --> Provenance[Provenance logger<br/>route, backend, runtime]
    Memory --> Router
    Classical --> Export[Mask/annotation export]
    Cellpose --> Export
    LangSAM --> Export
    MedSAM --> Export
    MedSAM2 --> Export
    Export --> Formats[PNG, NIfTI, TIFF stack,<br/>polygon JSON, COCO JSON]
    Export --> Provenance
```

Figure caption draft:

Architecture of the lightweight annotation workflow. Heavy model backends are optional and accessed through external command bridges by default. Provenance and memory store metadata and geometry rather than raw image pixels by default.
