"""Learner services package.

Submodules expose the learner-intelligence services: ConceptMastery/BKT
(``recompute_mastery`` lives on the model), weak-topic analysis, IRT, path
generation, prerequisites, revision scheduling, and the aggregate profile
service.

``LearnerProfileService`` is re-exported lazily (PEP 562) so that importing this
package never triggers model imports at app-load time -- model imports happen
only on first use, when the app registry is ready (avoids AppRegistryNotReady
during ``django.setup()``).
"""
__all__ = ["LearnerProfileService"]


def __getattr__(name):
    if name == "LearnerProfileService":
        from learner.services.learner_profile import LearnerProfileService
        return LearnerProfileService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")