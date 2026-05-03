"""Glossary engine: slug normalization, duplicate detection, semantic linking."""
from .slug_normalizer import normalize_slug, resolve_synonym
from .duplicate_detector import DuplicateDetector
from .semantic_linker import GlossarySemanticLinker

__all__ = ["normalize_slug", "resolve_synonym", "DuplicateDetector", "GlossarySemanticLinker"]
