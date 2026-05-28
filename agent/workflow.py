from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional, Sequence

from segmentation.backends import build_default_backends
from segmentation.backends.base import SegmentationResult

from .router import AgenticRouter, RoutingDecision


@dataclass
class WorkflowRun:
    result: SegmentationResult
    routing: RoutingDecision

    def to_summary(self) -> Dict[str, Any]:
        return {"result": self.result.to_summary(), "routing": self.routing.to_dict()}


class AgenticWorkflow:
    def __init__(self, backends: Optional[Dict[str, Any]] = None, router: Optional[AgenticRouter] = None):
        self.backends = backends or build_default_backends()
        self.router = router or AgenticRouter()
        self.last_routing: Optional[RoutingDecision] = None

    def backend_statuses(self) -> Dict[str, Any]:
        statuses = {}
        for name, backend in self.backends.items():
            try:
                statuses[name] = backend.check_available()
            except Exception as ex:
                from segmentation.backends.base import BackendStatus

                statuses[name] = BackendStatus(False, f"status check failed: {ex}")
        return statuses

    def segment(
        self,
        image,
        *,
        prompt: Optional[str] = None,
        bbox: Optional[Sequence[int]] = None,
        points=None,
        labels=None,
        seed=None,
        metadata: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> WorkflowRun:
        statuses = self.backend_statuses()
        decision = self.router.route(
            image,
            prompt=prompt,
            bbox=bbox,
            points=points,
            seed=seed,
            metadata=metadata,
            backend_statuses=statuses,
        )
        self.last_routing = decision
        cfg = dict(config or {})
        fallback_history = []
        last_error = None
        candidates = list(decision.ranked_candidates)
        if decision.selected_backend and decision.selected_backend not in candidates:
            candidates.insert(0, decision.selected_backend)
        for name in candidates:
            backend = self.backends.get(name)
            status = statuses.get(name)
            if backend is None:
                fallback_history.append({"backend": name, "status": "missing", "reason": "backend object not registered"})
                continue
            if status is not None and not status.available:
                fallback_history.append({"backend": name, "status": "unavailable", "reason": status.reason})
                continue
            try:
                result = backend.segment(
                    image,
                    prompt=prompt,
                    bbox=bbox,
                    points=points,
                    labels=labels,
                    config=cfg.get(name, cfg),
                )
                result.metadata.setdefault("workflow", {})
                result.metadata["workflow"]["fallback_attempts"] = list(fallback_history)
                decision.selected_backend = name
                decision.fallback_history = fallback_history
                return WorkflowRun(result=result, routing=decision)
            except Exception as ex:
                last_error = str(ex)
                fallback_history.append({"backend": name, "status": "failed", "reason": last_error})
        # Last-resort mock should exist in default configuration; if it also failed, re-raise.
        raise RuntimeError(f"all workflow backends failed: {fallback_history}")

    def explain_routing(
        self,
        image=None,
        *,
        prompt: Optional[str] = None,
        bbox=None,
        points=None,
        seed=None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> tuple[str, Dict[str, Any]]:
        if image is not None:
            decision = self.router.route(
                image,
                prompt=prompt,
                bbox=bbox,
                points=points,
                seed=seed,
                metadata=metadata,
                backend_statuses=self.backend_statuses(),
            )
        elif self.last_routing is not None:
            decision = self.last_routing
        else:
            raise ValueError("provide an image or run segment() before explain_routing()")
        lines = [
            f"Selected backend: {decision.selected_backend}",
            f"Image type guess: {decision.image_type_guess}",
            f"Reason: {decision.decision_reason}",
            f"Ranked candidates: {', '.join(decision.ranked_candidates)}",
        ]
        if decision.unavailable_backends:
            lines.append("Unavailable: " + ", ".join(f"{k} ({v})" for k, v in decision.unavailable_backends.items()))
        if decision.fallback_history:
            lines.append("Fallbacks: " + "; ".join(f"{x['backend']}={x['status']}" for x in decision.fallback_history))
        return "\n".join(lines), decision.to_dict()
