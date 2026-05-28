from difflib import SequenceMatcher
from typing import Dict, List, Optional


def retrieve_similar_prompt(events: List[dict], *, image_fingerprint: str = "", text_prompt: str = "", modality_guess: str = "") -> Optional[dict]:
    best = None
    best_score = -1.0
    query = (text_prompt or "").lower().strip()
    for event in events:
        score = 0.0
        if image_fingerprint and event.get("image_fingerprint") == image_fingerprint:
            score += 2.0
        if modality_guess and event.get("modality_guess") == modality_guess:
            score += 0.5
        candidate = (event.get("text_prompt") or "").lower().strip()
        if query and candidate:
            score += SequenceMatcher(None, query, candidate).ratio()
        if event.get("bbox"):
            score += 0.1
        if score > best_score:
            best_score = score
            best = dict(event)
    return best


def suggest_prompt_from_memory(events: List[dict], query: Dict[str, str]) -> Optional[dict]:
    hit = retrieve_similar_prompt(
        events,
        image_fingerprint=query.get("image_fingerprint", ""),
        text_prompt=query.get("text_prompt", ""),
        modality_guess=query.get("modality_guess", ""),
    )
    if not hit:
        return None
    return {
        "text_prompt": hit.get("text_prompt"),
        "bbox": hit.get("bbox"),
        "points": hit.get("points"),
        "selected_backend": hit.get("selected_backend"),
        "source_timestamp": hit.get("timestamp"),
    }
