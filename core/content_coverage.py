from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


_STATIC_PAGES: dict[str, str] = {
    "index": "Pipeleap | Sales Automation Platform for B2B Sales Teams",
    "services": "Services",
    "how-it-works": "How It Works",
    "results": "Results",
    "gtm-audit": "GTM Audit",
    "pricing": "Pricing",
    "about": "About",
    "contact": "Contact",
    "faq": "FAQ",
    "privacy": "Privacy",
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
        return {
            "total_pages": len(self.page_index),
            "total_slugs": len(self.covered_slugs),
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
