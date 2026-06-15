"""
论文检索服务 - arXiv & Semantic Scholar & CrossRef
放置位置: backend/app/services/paper_search.py

核心改进：
1. 中文→英文关键词映射（确保能搜到结果）
2. 三级降级搜索策略（精确→宽泛→领域通用）
3. 返回结果中标注与当前分析的关联说明
"""

import re
import asyncio
from typing import List, Optional
from dataclasses import dataclass, asdict
import httpx
import xml.etree.ElementTree as ET


@dataclass
class PaperResult:
    """论文搜索结果结构"""
    title: str
    authors: str
    year: str
    abstract: str
    url: str
    source: str           # "arXiv" / "Semantic Scholar" / "CrossRef"
    relevance: str        # 与当前分析的关联说明
    arxiv_id: str = ""
    doi: str = ""
    citation_count: int = 0


class PaperSearchService:
    """论文检索服务类"""

    # 中文→英文关键词映射表
    CN_EN_MAP = {
        "衬底温度": "substrate temperature",
        "基板温度": "substrate temperature",
        "生长温度": "growth temperature",
        "分子束外延": "molecular beam epitaxy MBE",
        "外延生长": "epitaxial growth",
        "汞镉碲": "HgCdTe mercury cadmium telluride",
        "碲镉汞": "HgCdTe mercury cadmium telluride",
        "红外探测器": "infrared detector",
        "组分控制": "composition control",
        "组分均匀性": "composition uniformity",
        "截止波长": "cutoff wavelength",
        "生长速率": "growth rate",
        "束流压力": "beam equivalent pressure BEP",
        "通量": "flux",
        "汞通量": "mercury Hg flux",
        "粘附系数": "sticking coefficient",
        "空位": "vacancy defect",
        "缺陷": "defect",
        "表面重构": "surface reconstruction",
        "晶格匹配": "lattice matching",
        "位错": "dislocation",
        "退火": "annealing",
        "能带": "bandgap",
    }

    # 领域通用备用搜索词（保底用）
    FALLBACK_QUERIES = [
        "HgCdTe MBE molecular beam epitaxy growth",
        "HgCdTe infrared detector epitaxial",
        "mercury cadmium telluride substrate temperature optimization",
        "MCT MBE Hg flux sticking coefficient",
        "CdZnTe substrate HgCdTe epitaxy",
    ]

    def __init__(self):
        self.arxiv_base = "http://export.arxiv.org/api/query"
        self.semantic_base = "https://api.semanticscholar.org/graph/v1/paper/search"
        self.crossref_base = "https://api.crossref.org/works"

    async def search(
        self,
        query: str,
        max_results: int = 5,
        sources: List[str] = None
    ) -> List[dict]:
        """
        主搜索入口 - 三级降级策略
        """
        if sources is None:
            sources = ["arxiv", "semantic_scholar"]

        # 第一次：精确搜索
        results = await self._do_search(query, max_results, sources)

        # 第二次：如果结果不足，尝试简化查询
        if len(results) < 2:
            simplified = self._simplify_query(query)
            if simplified != query:
                more = await self._do_search(simplified, max_results, sources)
                results.extend(more)

        # 第三次：如果仍然不足，使用领域备用词
        if len(results) < 2:
            import random
            fallback = random.choice(self.FALLBACK_QUERIES)
            more = await self._do_search(fallback, max_results, sources)
            for p in more:
                p.relevance = "（领域通用参考文献）"
            results.extend(more)

        # 去重
        unique = self._deduplicate(results)
        unique.sort(key=lambda x: x.citation_count, reverse=True)

        return [asdict(p) for p in unique[:max_results]]

    async def _do_search(self, query: str, max_results: int, sources: List[str]) -> List[PaperResult]:
        """执行实际搜索"""
        tasks = []
        if "arxiv" in sources:
            tasks.append(self._search_arxiv(query, max_results))
        if "semantic_scholar" in sources:
            tasks.append(self._search_semantic_scholar(query, max_results))
        if "crossref" in sources:
            tasks.append(self._search_crossref(query, max_results))

        results_nested = await asyncio.gather(*tasks, return_exceptions=True)

        all_results = []
        for result in results_nested:
            if isinstance(result, Exception):
                continue
            all_results.extend(result)

        return all_results

    async def _search_arxiv(self, query: str, max_results: int) -> List[PaperResult]:
        """搜索 arXiv"""
        papers = []
        # arXiv 查询：不限定分类以获得更多结果
        search_query = f'all:{query}'

        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(self.arxiv_base, params=params)
                if resp.status_code != 200:
                    return []

                root = ET.fromstring(resp.text)
                ns = {"atom": "http://www.w3.org/2005/Atom"}

                for entry in root.findall("atom:entry", ns):
                    title = entry.find("atom:title", ns)
                    summary = entry.find("atom:summary", ns)
                    published = entry.find("atom:published", ns)
                    link = entry.find("atom:id", ns)

                    authors_elems = entry.findall("atom:author/atom:name", ns)
                    authors_list = [a.text.strip() for a in authors_elems[:3]]
                    if len(authors_elems) > 3:
                        authors_list.append("et al.")

                    title_text = title.text.strip().replace("\n", " ") if title is not None else ""
                    abstract_text = summary.text.strip().replace("\n", " ")[:500] if summary is not None else ""
                    year = published.text[:4] if published is not None else ""
                    url = link.text.strip() if link is not None else ""

                    # 跳过无标题的结果
                    if not title_text or title_text.startswith("Error"):
                        continue

                    arxiv_id = url.split("/abs/")[-1] if "/abs/" in url else ""

                    papers.append(PaperResult(
                        title=title_text,
                        authors=", ".join(authors_list),
                        year=year,
                        abstract=abstract_text,
                        url=url,
                        source="arXiv",
                        relevance="",
                        arxiv_id=arxiv_id,
                    ))
        except Exception as e:
            print(f"[PaperSearch] arXiv 搜索异常: {e}")

        return papers

    async def _search_semantic_scholar(self, query: str, max_results: int) -> List[PaperResult]:
        """搜索 Semantic Scholar"""
        papers = []

        params = {
            "query": query,
            "limit": max_results,
            "fields": "title,authors,year,abstract,url,externalIds,citationCount",
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(self.semantic_base, params=params)
                if resp.status_code != 200:
                    return []

                data = resp.json()
                for item in data.get("data", []):
                    if not item.get("title"):
                        continue

                    authors_list = [a.get("name", "") for a in item.get("authors", [])[:3]]
                    if len(item.get("authors", [])) > 3:
                        authors_list.append("et al.")

                    abstract = item.get("abstract") or ""
                    external_ids = item.get("externalIds") or {}

                    paper_url = item.get("url", "")
                    if not paper_url and external_ids.get("DOI"):
                        paper_url = f"https://doi.org/{external_ids['DOI']}"
                    elif not paper_url:
                        paper_url = f"https://www.semanticscholar.org/paper/{item.get('paperId', '')}"

                    papers.append(PaperResult(
                        title=item.get("title", ""),
                        authors=", ".join(authors_list),
                        year=str(item.get("year", "")),
                        abstract=abstract[:500],
                        url=paper_url,
                        source="Semantic Scholar",
                        relevance="",
                        arxiv_id=external_ids.get("ArXiv", ""),
                        doi=external_ids.get("DOI", ""),
                        citation_count=item.get("citationCount", 0),
                    ))
        except Exception as e:
            print(f"[PaperSearch] Semantic Scholar 搜索异常: {e}")

        return papers

    async def _search_crossref(self, query: str, max_results: int) -> List[PaperResult]:
        """搜索 CrossRef（补充源）"""
        papers = []

        params = {
            "query.bibliographic": query,
            "rows": max_results,
            "sort": "relevance",
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(self.crossref_base, params=params)
                if resp.status_code != 200:
                    return []

                data = resp.json()
                items = data.get("message", {}).get("items", [])

                for item in items:
                    title_list = item.get("title", [])
                    title = title_list[0] if title_list else ""
                    if not title:
                        continue

                    authors_raw = item.get("author", [])
                    authors_list = []
                    for a in authors_raw[:3]:
                        name = f"{a.get('given', '')} {a.get('family', '')}".strip()
                        if name:
                            authors_list.append(name)
                    if len(authors_raw) > 3:
                        authors_list.append("et al.")

                    # 年份
                    date_parts = item.get("published-print", {}).get("date-parts", [[]])
                    if not date_parts[0]:
                        date_parts = item.get("published-online", {}).get("date-parts", [[]])
                    year = str(date_parts[0][0]) if date_parts[0] else ""

                    doi = item.get("DOI", "")
                    url = f"https://doi.org/{doi}" if doi else ""

                    papers.append(PaperResult(
                        title=title,
                        authors=", ".join(authors_list),
                        year=year,
                        abstract="",  # CrossRef 通常不返回摘要
                        url=url,
                        source="CrossRef",
                        relevance="",
                        doi=doi,
                        citation_count=item.get("is-referenced-by-count", 0),
                    ))
        except Exception as e:
            print(f"[PaperSearch] CrossRef 搜索异常: {e}")

        return papers

    def _simplify_query(self, query: str) -> str:
        """简化查询：取前3个关键词"""
        words = query.split()
        if len(words) > 4:
            return " ".join(words[:4])
        return query

    def _deduplicate(self, papers: List[PaperResult]) -> List[PaperResult]:
        """去重"""
        seen = set()
        unique = []
        for p in papers:
            key = p.title[:50].lower().strip()
            if key not in seen:
                seen.add(key)
                unique.append(p)
        return unique

    def extract_search_keywords(self, ai_response: str, user_query: str = "") -> List[str]:
        """
        从 AI 回复中提取适合论文检索的英文关键词
        核心改进：中文→英文映射
        """
        keywords = []
        combined_text = ai_response + " " + user_query

        # 1. 中文关键词→英文映射
        found_en_terms = []
        for cn, en in self.CN_EN_MAP.items():
            if cn in combined_text:
                found_en_terms.append(en)

        # 2. 直接提取英文术语
        en_terms = re.findall(r'\b[A-Z][a-zA-Z]{2,}(?:\s+[a-zA-Z]+){0,2}\b', combined_text)
        # 过滤常见非术语词
        stop_words = {"The", "This", "That", "And", "For", "With", "From", "About", "Step", "Please"}
        en_terms = [t for t in en_terms if t not in stop_words and len(t) > 3]

        # 3. 构建搜索查询
        # 策略A：如果找到了领域映射词，用它们组合
        if found_en_terms:
            # 取最具体的2-3个词组合
            primary = found_en_terms[0]
            if "HgCdTe" in combined_text or "碲镉汞" in combined_text or "汞镉碲" in combined_text:
                keywords.append(f"HgCdTe {primary}")
            else:
                keywords.append(primary)

            if len(found_en_terms) > 1:
                keywords.append(f"HgCdTe {found_en_terms[1]}")

        # 策略B：加入直接出现的英文术语
        hgcdt_related = [t for t in en_terms if any(k in t for k in ["Hg", "Cd", "Te", "MBE", "RHEED", "BEP"])]
        if hgcdt_related:
            keywords.append(" ".join(hgcdt_related[:3]))

        # 策略C：保底
        if not keywords:
            keywords.append("HgCdTe MBE growth")

        # 确保有 HgCdTe 上下文
        final_keywords = []
        for kw in keywords[:3]:
            if "HgCdTe" not in kw and "MCT" not in kw and "mercury" not in kw.lower():
                kw = f"HgCdTe {kw}"
            final_keywords.append(kw)

        return final_keywords[:3]


# 模块级单例
paper_service = PaperSearchService()