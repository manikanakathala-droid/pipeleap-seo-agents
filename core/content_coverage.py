from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from itertools import chain
from pathlib import Path
from typing import Any


_STATIC_PAGES: dict[str, str] = {
    "index": "Pipeleap | Sales Automation Platform for B2B Sales Teams",
    "services": "Services",
    "how-it-works": "How It Works",
    "sales-ops-audit": "Sales Ops Audit",
    "pricing": "Pricing",
    "about": "About",
    "contact": "Contact",
    "faq": "FAQ",
    "tools": "Tools",
    "glossary": "Glossary",
    "case-studies": "Case Studies",
    "privacy": "Privacy",
    "terms": "Terms of Service",
}


@dataclass
class PageInfo:
    slug: str
    title: str
    page_type: str
    description: str = ""
    terms: list[str] = field(default_factory=list)


@dataclass
class ContentCoverage:
    page_index: dict[str, PageInfo] = field(default_factory=dict)
    covered_slugs: set[str] = field(default_factory=set)
    covered_keywords: set[str] = field(default_factory=set)
    _data_dir: Path | None = field(default=None, repr=False)

    def check_keyword(self, keyword: str) -> dict[str, Any]:
        kw_slug = _slugify(keyword)
        kw_lower = keyword.lower()
        kw_words = set(kw_lower.split())

        if kw_slug in self.covered_slugs:
            info = self.page_index[kw_slug]
            return {
                "status": "covered",
                "match_type": "slug",
                "matched_slug": kw_slug,
                "page_title": info.title,
                "page_type": info.page_type,
                "confidence": 1.0,
            }

        slug_parts = kw_slug.split("-")
        slug_prefix = slug_parts[0] if len(slug_parts) > 1 else ""
        if slug_prefix and len(slug_prefix) >= 3:
            match_by_prefix = sorted(
                [s for s in self.covered_slugs if s.startswith(slug_prefix) and s in self.page_index and len(s) >= 5],
                key=lambda s: len(s),
            )
            if match_by_prefix:
                info = self.page_index[match_by_prefix[0]]
                return {
                    "status": "partial",
                    "match_type": "slug_prefix",
                    "matched_slug": match_by_prefix[0],
                    "page_title": info.title,
                    "page_type": info.page_type,
                    "confidence": 0.5,
                }

        best: dict[str, Any] | None = None
        best_overlap = 0
        for info in self.page_index.values():
            info_words = set(_tokenize(info.title)) | set(_tokenize(info.description))
            common = kw_words & info_words
            overlap = len(common) / max(len(kw_words), 1)
            if overlap > best_overlap:
                best_overlap = overlap
                best = {
                    "status": "partial" if overlap >= 0.5 else "gap",
                    "match_type": "title_overlap",
                    "matched_terms": list(common),
                    "page_title": info.title,
                    "page_type": info.page_type,
                    "matched_slug": info.slug,
                    "confidence": round(overlap, 2),
                }

        if best:
            return best

        return {
            "status": "gap",
            "match_type": None,
            "confidence": 0.0,
        }

    def to_dict(self) -> dict[str, Any]:
        corpus_len = 0
        if self._data_dir:
            corpus_len = len(self._build_corpus(self._data_dir))
        return {
            "total_pages": len(self.page_index),
            "total_slugs": len(self.covered_slugs),
            "corpus_chars": corpus_len,
            "by_type": {
                pt: len([p for p in self.page_index.values() if p.page_type == pt])
                for pt in {p.page_type for p in self.page_index.values()}
            },
        }

    @staticmethod
    def build(launchpad_root: str | Path) -> ContentCoverage:
        root = Path(launchpad_root)
        coverage = ContentCoverage()
        data_dir = root / "src" / "data"

        coverage._load_glossary(data_dir)
        coverage._load_blog_articles(data_dir)
        coverage._load_tools(data_dir)
        coverage._load_static_pages()

        coverage._data_dir = data_dir
        return coverage

    # ── Internal loaders ─────────────────────────────────────────────────

    def _load_glossary(self, data_dir: Path) -> None:
        path = data_dir / "glossary-terms.ts"
        if not path.exists():
            return
        text = path.read_text(encoding="utf-8")

        slug_pattern = re.compile(r'slug:\s*["`]([a-z0-9-]+)["`]')
        term_pattern = re.compile(r'term:\s*["`]([^"`]+)["`]')
        slug_iter = iter(slug_pattern.findall(text))

        for term_match in term_pattern.finditer(text):
            try:
                slug = next(slug_iter)
            except StopIteration:
                break
            term_text = term_match.group(1)
            self.page_index[slug] = PageInfo(
                slug=slug,
                title=term_text,
                page_type="glossary",
                terms=_tokenize(term_text),
            )
            self.covered_slugs.add(slug)
            self.covered_keywords.add(term_text.lower())

    def _load_blog_articles(self, data_dir: Path) -> None:
        path = data_dir / "blog-articles.ts"
        if not path.exists():
            return
        text = path.read_text(encoding="utf-8")

        slug_pattern = re.compile(r'slug["`]?\s*:\s*["`]([a-z0-9-]+)["`]')
        title_pattern = re.compile(r'title["`]?\s*:\s*["`]([^"`]+)["`]')
        desc_pattern = re.compile(r'description["`]?\s*:\s*["`]([^"`]+)["`]')

        slugs = slug_pattern.findall(text)
        titles = title_pattern.findall(text)
        descs = desc_pattern.findall(text)

        for i, slug in enumerate(slugs):
            title = titles[i] if i < len(titles) else slug
            desc = descs[i] if i < len(descs) else ""
            self.page_index[slug] = PageInfo(
                slug=slug,
                title=title,
                description=desc,
                page_type="blog",
                terms=_tokenize(title) + _tokenize(desc),
            )
            self.covered_slugs.add(slug)
            for word in _tokenize(title):
                self.covered_keywords.add(word.lower() if isinstance(word, str) else word)

    def _load_tools(self, data_dir: Path) -> None:
        tools_dir = data_dir / "tools"
        if not tools_dir.exists():
            return

        cat_path = tools_dir / "categories.ts"
        if cat_path.exists():
            text = cat_path.read_text(encoding="utf-8")
            cat_slug_pat = re.compile(r'slug["`]?\s*:\s*["`]([a-z0-9-]+)["`]')
            cat_name_pat = re.compile(r'name["`]?\s*:\s*["`]([^"`]+)["`]')
            cat_slugs = cat_slug_pat.findall(text)
            cat_names = cat_name_pat.findall(text)
            for i, name in enumerate(cat_names):
                slug = cat_slugs[i] if i < len(cat_slugs) else _slugify(name)
                self.page_index[f"tools/{slug}"] = PageInfo(
                    slug=f"tools/{slug}",
                    title=name,
                    page_type="tool_category",
                    terms=_tokenize(name),
                )
                self.covered_slugs.add(f"tools/{slug}")
                self.covered_slugs.add(slug)
                for word in _tokenize(name):
                    self.covered_keywords.add(word.lower())

            for ts_file in tools_dir.glob("*.ts"):
                if ts_file.name == "categories.ts" or ts_file.name == "index.ts":
                    continue
                text = ts_file.read_text(encoding="utf-8")
                slug_pattern = re.compile(r'slug["`]?\s*:\s*["`]([a-z0-9-]+)["`]')
                name_pattern = re.compile(r'name["`]?\s*:\s*["`]([^"`]+)["`]')
                slugs = slug_pattern.findall(text)
                names = name_pattern.findall(text)

                for i, slug in enumerate(slugs):
                    name = names[i] if i < len(names) else slug
                    self.page_index[f"tools/{slug}"] = PageInfo(
                        slug=f"tools/{slug}",
                        title=name,
                        page_type="tool",
                        terms=_tokenize(name),
                    )
                    self.covered_slugs.add(f"tools/{slug}")
                    self.covered_slugs.add(slug)
                    for word in _tokenize(name):
                        self.covered_keywords.add(word.lower())

    def _load_static_pages(self) -> None:
        for slug, title in _STATIC_PAGES.items():
            self.page_index[slug] = PageInfo(
                slug=slug,
                title=title,
                page_type="page",
                terms=_tokenize(title),
            )
            self.covered_slugs.add(slug)
            for word in _tokenize(title):
                self.covered_keywords.add(word.lower())

    # ── Text extraction for latent keyword mining ────────────────────────

    def _extract_blog_text(self, data_dir: Path) -> str:
        path = data_dir / "blog-articles.ts"
        if not path.exists():
            return ""
        text = path.read_text(encoding="utf-8")
        text_fields = re.findall(r'text["`]?\s*:\s*["`]([^"`]{10,})["`]', text)
        return " ".join(text_fields)

    def _extract_glossary_text(self, data_dir: Path) -> str:
        path = data_dir / "glossary-terms.ts"
        if not path.exists():
            return ""
        text = path.read_text(encoding="utf-8")
        definitions = re.findall(r'definition["`]?\s*:\s*["`]([^"`]{20,})["`]', text)
        return " ".join(definitions)

    def _extract_tool_text(self, data_dir: Path) -> str:
        tools_dir = data_dir / "tools"
        if not tools_dir.exists():
            return ""
        chunks: list[str] = []
        for ts_file in tools_dir.glob("*.ts"):
            if ts_file.name == "index.ts":
                continue
            text = ts_file.read_text(encoding="utf-8")
            descs = re.findall(r'(?:description|intro|body|pipeLeapAngle)["`]?\s*:\s*["`]([^"`]{20,})["`]', text)
            chunks.extend(descs)
            list_items = re.findall(r'["`]([A-Z][^"`]{10,})["`]', text)
            for item in list_items:
                if len(item.split()) >= 3:
                    chunks.append(item)
        return " ".join(chunks)

    def _build_corpus(self, data_dir: Path | None = None) -> str:
        texts: list[str] = []
        if data_dir:
            texts.append(self._extract_blog_text(data_dir))
            texts.append(self._extract_glossary_text(data_dir))
            texts.append(self._extract_tool_text(data_dir))
        return " ".join(t for t in texts if t)

    def mine_latent_keywords(
        self,
        data_dir: Path | None = None,
        top_n: int = 20,
        min_freq: int = 2,
    ) -> list[dict[str, Any]]:
        corpus = self._build_corpus(data_dir)
        if not corpus or len(corpus) < 500:
            return []

        tokens = _tokenize(corpus)
        tokens = [t for t in tokens if t not in _DOMAIN_STOP_WORDS and len(t) > 1]

        bigrams = [" ".join(tokens[i:i + 2]) for i in range(len(tokens) - 1) if len(tokens[i]) > 2 and len(tokens[i + 1]) > 2]
        trigrams = [" ".join(tokens[i:i + 3]) for i in range(len(tokens) - 2) if all(len(tokens[i + j]) > 2 for j in range(3))]

        bg_counts = Counter(bigrams)
        tg_counts = Counter(trigrams)

        def _intent_bonus(phrase: str) -> float:
            high_intent = {"best", "vs", "versus", "alternative", "alternatives", "review", "pricing", "cost", "compare", "comparison", "top", "demo", "trial", "buy", "signup", "book"}
            words = set(phrase.split())
            overlap = words & high_intent
            return 1.5 if overlap else 1.0

        def _is_covered(phrase: str) -> bool:
            slug = _slugify(phrase)
            if slug in self.covered_slugs:
                return True
            if phrase.lower() in self.covered_keywords:
                return True
            for existing in self.covered_slugs:
                if slug in existing or existing in slug:
                    return True
            return False

        candidates: list[dict[str, Any]] = []
        seen: set[str] = set()

        for phrase, freq in chain(bg_counts.items(), tg_counts.items()):
            if freq < min_freq:
                continue
            if phrase in seen:
                continue
            seen.add(phrase)
            if _is_covered(phrase):
                continue
            bonus = _intent_bonus(phrase)
            candidates.append({
                "keyword": phrase,
                "frequency": freq,
                "intent_bonus": bonus,
                "score": round(freq * bonus, 1),
                "source": "content_mining",
            })

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:top_n]


_DOMAIN_STOP_WORDS: set[str] = {
    # Common English stop words
    "the", "and", "for", "are", "was", "were", "been", "being", "have",
    "has", "had", "having", "do", "does", "did", "doing", "will", "would",
    "can", "could", "shall", "should", "may", "might", "must", "need",
    "dare", "ought", "used", "this", "that", "these", "those", "what",
    "which", "who", "whom", "whose", "when", "where", "why", "how",
    "all", "each", "every", "both", "few", "more", "most", "other",
    "some", "such", "no", "nor", "not", "only", "own", "same", "so",
    "than", "too", "very", "just", "because", "as", "until", "while",
    "of", "at", "by", "with", "about", "against", "between", "into",
    "through", "during", "before", "after", "above", "below", "from",
    "up", "down", "in", "out", "on", "off", "over", "under", "again",
    "further", "then", "once", "here", "there", "when", "where", "why",
    "how", "all", "any", "both", "each", "few", "more", "most", "other",
    "some", "such", "no", "nor", "not", "only", "own", "same",
    "but", "nor", "or", "yet", "so",
    "your", "current", "specific", "multiple", "various", "multiple",
    # Domain-specific noise
    "tool", "tools", "system", "systems", "platform", "platforms", "software",
    "team", "teams", "process", "processes", "data", "workflow",
    "workflows", "automation", "need", "needs", "use", "using",
    "help", "helps", "helping", "make", "makes", "making", "get",
    "gets", "getting", "way", "ways", "thing", "things",
    "like", "well", "also", "even", "much", "many",
    "still", "already", "actually", "however", "without", "within", "back",
    "every", "going", "around", "across", "along", "always", "another",
    "become", "becomes", "becoming", "might", "must", "never", "next",
    "often", "once", "really", "said", "says", "since", "something",
    "sometimes", "start", "starts", "starting", "take", "takes", "taking",
    "tell", "tells", "telling", "toward", "towards", "usually", "various",
    "without", "worth", "yet", "away", "able", "asked", "begin", "behind",
    "believe", "beyond", "bring", "brings", "coming", "common", "could",
    "course", "day", "days", "deals", "doing", "down", "else", "enough",
    "example", "fact", "feel", "gave", "given", "giving",
    "good", "great", "group", "groups", "happens", "hard",
    "high", "hold", "idea", "important", "interest",
    "keep", "keeps", "kept", "kind", "kinds",
    "know", "known", "knows", "large", "last", "later", "leave", "left",
    "less", "let", "life", "likely", "line", "long", "longer",
    "looks", "made", "main", "matter", "mean", "means", "meet", "meets",
    "months", "most", "move", "moving", "name", "near", "necessary",
    "number", "numbers", "order", "orders", "part", "particular", "parts",
    "past", "per", "place", "places", "point", "points", "possible",
    "present", "problem", "problems", "put", "puts", "question", "questions",
    "rather", "reason", "reasons", "result", "results", "right", "run",
    "running", "runs", "saw", "say", "seeing", "seem", "seems", "seen",
    "sense", "serious", "set", "sets", "short", "show", "shows", "shown",
    "side", "significant", "similar", "simple", "simply", "small", "sure",
    "talk", "talks", "talking", "term", "terms", "type", "types", "understand",
    "understanding", "value", "values", "view", "views", "wait", "waiting",
    "walk", "walking", "want", "wants", "weeks", "whole", "wide", "word",
    "words", "work", "works", "working", "year", "years",
}


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "page"


def _tokenize(text: str) -> list[str]:
    return [w for w in re.sub(r"[^a-z0-9 ]+", " ", text.lower()).split() if len(w) > 1]


def detect_content_gaps(
    keywords: list[dict[str, Any]],
    coverage: ContentCoverage,
    min_confidence: float = 0.0,
) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for kw in keywords:
        keyword_text = kw.get("keyword", "")
        if not keyword_text:
            continue
        result = coverage.check_keyword(keyword_text)
        if result["status"] == "gap":
            gaps.append({**kw, "coverage": result})
        elif result["status"] == "partial" and result["confidence"] <= min_confidence:
            gaps.append({**kw, "coverage": result})
        else:
            kw["coverage"] = result
    return sorted(gaps, key=lambda x: x.get("difficulty", 100) if isinstance(x.get("difficulty"), (int, float)) else 0, reverse=False)
