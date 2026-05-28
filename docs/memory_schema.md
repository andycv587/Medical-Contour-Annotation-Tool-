# Memory Schema

The canonical memory schema lives in `memory/`.

`python_app/agent_memory.py` remains as the Tkinter GUI adapter for compatibility. GUI records can be mapped to canonical `MemoryEvent` objects through `MemoryRecord.to_memory_event()`.

## Stored By Default

- image fingerprint;
- image shape when available;
- modality guess;
- text prompt;
- bbox;
- points/seeds when available;
- selected backend and backend version;
- model checkpoint identifier when available;
- segmentation parameters;
- runtime;
- mask summary statistics;
- correction count when available;
- timestamp;
- project/session id;
- provenance id/reference when available.

## Privacy Behavior

Raw image pixels/voxels are not saved by default. `MemoryEvent.to_dict(include_raw=False)` removes any raw image payload and sets `raw_image_saved` to `false`.

Memory suggests prompts and bounding boxes. It must not silently overwrite masks or apply saved masks without user action.

## GUI Behavior

The GUI exposes memory toggles for:

- using agentic memory;
- persisting long-term memory.

Disabling memory should prevent new GUI memory suggestions and records. Long-term global memory remains optional; project/session-specific memory is the preferred default for publication workflows.
