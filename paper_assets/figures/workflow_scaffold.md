# Figure 2 Workflow Scaffold

Status: scaffold only. Quantitative panels must be generated from actual benchmark outputs.

```mermaid
sequenceDiagram
    participant User
    participant GUI as Tkinter GUI
    participant Router as Agentic router
    participant Memory as Project/session memory
    participant Backend as Selected backend
    participant Prov as Provenance logger
    participant Export as Export layer

    User->>GUI: Load public image/volume
    User->>GUI: Draw prompt, bbox, or text prompt
    GUI->>Memory: Query prompt/bbox suggestion
    Memory-->>GUI: Optional suggestion
    GUI->>Router: Request segmentation with context
    Router->>Backend: Select backend or fallback
    Backend-->>GUI: Candidate mask/instances
    GUI->>Prov: Log route, backend, runtime, preview state
    User->>GUI: Accept/reject/correct preview
    GUI->>Memory: Store geometry and mask summary
    User->>Export: Export required format
    Export->>Prov: Log export action and output path
```

Figure caption draft:

Annotation workflow for manual and model-assisted segmentation. The router exposes the selected backend and fallback rationale, memory suggests prior geometry without silently overwriting masks, and provenance records the route, runtime, preview decision, and export action.
