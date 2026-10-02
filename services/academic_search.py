import re
import html
import httpx
from typing import List, Dict, Any, Optional

def reconstruct_openalex_abstract(inverted_index: Optional[Dict[str, List[int]]]) -> str:
    """Reconstructs text from OpenAlex's abstract_inverted_index."""
    if not inverted_index or not isinstance(inverted_index, dict):
        return ""
    words = []
    for word, positions in inverted_index.items():
        for pos in positions:
            words.append((pos, word))
    words.sort(key=lambda x: x[0])
    return " ".join(word for _, word in words)

def clean_html(raw_html: str) -> str:
    """Removes HTML and XML tags from abstracts."""
    if not raw_html:
        return ""
    clean = re.sub(r'<[^>]+>', ' ', raw_html)
    clean = html.unescape(clean)
    return " ".join(clean.split())

def format_short_citation(authors: List[str], year: Optional[int]) -> str:
    """Formats author and year into short citation (e.g., 'Cedillo et al., 2024' or 'Parra & Gómez, 2023')."""
    y_str = str(year) if year else "s.f."
    if not authors:
        return f"Anónimo, {y_str}"
    
    first_surname = authors[0].split()[-1] if authors[0] else "Autor"
    # If first name contains a comma like 'Cedillo, E.', extract before comma
    if "," in authors[0]:
        first_surname = authors[0].split(",")[0].strip()
        
    if len(authors) == 1:
        return f"{first_surname}, {y_str}"
    elif len(authors) == 2:
        second_surname = authors[1].split(",")[0].strip() if "," in authors[1] else authors[1].split()[-1]
        return f"{first_surname} & {second_surname}, {y_str}"
    else:
        return f"{first_surname} et al., {y_str}"

async def search_openalex(
    query: str,
    year_from: int = 2020,
    year_to: int = 2026,
    language: str = "all",
    limit: int = 25,
    require_doi: bool = True
) -> List[Dict[str, Any]]:
    """Searches OpenAlex works API."""
    results = []
    filter_parts = [f"from_publication_date:{year_from}-01-01", f"to_publication_date:{year_to}-12-31"]
    
    if language == "es":
        filter_parts.append("language:es")
    elif language == "en":
        filter_parts.append("language:en")
        
    filter_param = ",".join(filter_parts)
    url = "https://api.openalex.org/works"
    params = {
        "search": query,
        "filter": filter_param,
        "per_page": min(limit, 50),
        "sort": "relevance_score:desc"
    }
    
    headers = {
        "User-Agent": "AcademicMatrixExtractor/1.0 (mailto:academic-researcher@domain.com)"
    }
    
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("results", []):
                    doi = item.get("doi") or ""
                    if require_doi and not doi:
                        continue
                    
                    authors = []
                    for auth in item.get("authorships", []):
                        name = auth.get("author", {}).get("display_name")
                        if name:
                            authors.append(name)
                            
                    year = item.get("publication_year")
                    title = item.get("title") or "Sin título"
                    abstract = reconstruct_openalex_abstract(item.get("abstract_inverted_index"))
                    
                    venue_name = "Publicación académica"
                    host = item.get("primary_location") or {}
                    source = host.get("source") or {}
                    if source.get("display_name"):
                        venue_name = source.get("display_name")
                        
                    results.append({
                        "id": item.get("id"),
                        "title": title,
                        "authors": authors,
                        "author_citation": format_short_citation(authors, year),
                        "year": year,
                        "doi": doi.replace("https://doi.org/", "") if doi else "",
                        "url": doi or (item.get("primary_location") or {}).get("landing_page_url") or "",
                        "venue": venue_name,
                        "abstract": abstract,
                        "source": "OpenAlex",
                        "language": item.get("language") or "es"
                    })
    except Exception as e:
        print(f"Error querying OpenAlex: {e}")
        
    return results

async def search_crossref(
    query: str,
    year_from: int = 2020,
    year_to: int = 2026,
    limit: int = 25,
    require_doi: bool = True
) -> List[Dict[str, Any]]:
    """Searches Crossref works API."""
    results = []
    url = "https://api.crossref.org/works"
    params = {
        "query": query,
        "rows": min(limit, 50),
        "filter": f"from-pub-date:{year_from}-01-01,until-pub-date:{year_to}-12-31",
        "sort": "relevance",
        "order": "desc"
    }
    headers = {
        "User-Agent": "AcademicMatrixExtractor/1.0 (mailto:academic-researcher@domain.com)"
    }
    
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("message", {}).get("items", [])
                for item in items:
                    doi = item.get("DOI") or ""
                    if require_doi and not doi:
                        continue
                        
                    titles = item.get("title") or []
                    title = titles[0] if titles else "Sin título"
                    
                    authors = []
                    for a in item.get("author", []):
                        given = a.get("given", "")
                        family = a.get("family", "")
                        if family and given:
                            authors.append(f"{family}, {given}")
                        elif family:
                            authors.append(family)
                        elif given:
                            authors.append(given)
                            
                    pub_parts = (item.get("published") or item.get("issued") or {}).get("date-parts", [[]])
                    year = pub_parts[0][0] if pub_parts and pub_parts[0] else None
                    
                    container = item.get("container-title") or []
                    venue_name = container[0] if container else "Revista Científica"
                    
                    abstract = clean_html(item.get("abstract", ""))
                    item_url = item.get("URL") or (f"https://doi.org/{doi}" if doi else "")
                    
                    results.append({
                        "id": f"crossref:{doi}" if doi else title,
                        "title": title,
                        "authors": authors,
                        "author_citation": format_short_citation(authors, year),
                        "year": year,
                        "doi": doi,
                        "url": item_url,
                        "venue": venue_name,
                        "abstract": abstract,
                        "source": "Crossref",
                        "language": "es"
                    })
    except Exception as e:
        print(f"Error querying Crossref: {e}")
        
    return results

async def search_academic_literature(
    query: str,
    expanded_queries: Optional[List[str]] = None,
    year_from: int = 2020,
    year_to: int = 2026,
    language: str = "all",
    articles_per_source: int = 25,
    require_doi: bool = True
) -> List[Dict[str, Any]]:
    """Searches both OpenAlex and Crossref simultaneously with de-duplication."""
    queries_to_run = [query]
    if expanded_queries:
        for q in expanded_queries:
            if q and q.lower() not in [x.lower() for x in queries_to_run]:
                queries_to_run.append(q)
                
    # Search with primary query and top expanded query
    search_terms = queries_to_run[:2]
    all_articles = []
    
    for q_term in search_terms:
        # Search OpenAlex
        oa_results = await search_openalex(
            query=q_term,
            year_from=year_from,
            year_to=year_to,
            language=language,
            limit=articles_per_source,
            require_doi=require_doi
        )
        all_articles.extend(oa_results)
        
        # Search Crossref
        cr_results = await search_crossref(
            query=q_term,
            year_from=year_from,
            year_to=year_to,
            limit=articles_per_source,
            require_doi=require_doi
        )
        all_articles.extend(cr_results)
        
    # De-duplicate by DOI or normalized title
    seen_keys = set()
    unique_articles = []
    
    for art in all_articles:
        doi_clean = (art.get("doi") or "").lower().strip()
        title_clean = re.sub(r'[^a-zA-Z0-9]', '', (art.get("title") or "").lower())
        
        key = doi_clean if doi_clean else title_clean
        if not key or key in seen_keys:
            continue
            
        seen_keys.add(key)
        unique_articles.append(art)
        
    return unique_articles
