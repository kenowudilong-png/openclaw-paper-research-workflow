---
name: paper-research-workflow
description: Search academic papers, download PDFs, and write the results into a Notion paper database with PDF attachments when available.
metadata: { "openclaw": { "emoji": "📚", "primaryEnv": "NOTION_TOKEN", "requires": { "bins": ["bash", "python3"] } } }
---

# Paper Research Workflow

Use this skill when the user asks for paper search, literature review support, PDF download, or Notion paper database import.

## First Run

Install Python dependencies:

```bash
bash {baseDir}/scripts/bootstrap.sh
```

Check readiness:

```bash
bash {baseDir}/scripts/doctor.sh
```

## Commands

Search papers:

```bash
bash {baseDir}/scripts/search.sh --query "llm agents" --limit 12 --year-from 2024 --year-to 2025 --save
```

Download a PDF:

```bash
bash {baseDir}/scripts/download.sh --pdf-url "https://arxiv.org/pdf/2402.01680" --title "example"
```

Write a paper into Notion:

```bash
bash {baseDir}/scripts/write_notion.sh --paper-json '{"title":"Example Paper","authors":"A, B","year":2025,"pdf_path":"/tmp/example.pdf"}'
```

## Workflow

1. Parse the user's request into topic, count, year range, and any constraints.
2. Search at least `2x` the requested count whenever possible.
3. Read the search results and score them by relevance, recency, and impact using title, abstract, venue, and citation count.
4. Download the selected papers:
   - Prefer `open_access_pdf`
   - Then DOI
   - Then title fallback
5. Write selected papers into Notion:
   - If a `files` property exists in the database, attach the uploaded PDF there
   - Otherwise append the PDF as a file block inside the page
6. Report the final result in Chinese with title, year, score, and download/import status.

## Notes

- Notion requires a valid Integration Token plus a writable database URL or database ID.
- Database schema is matched loosely across Chinese and English property names.
- Results default to `output/results/` and PDFs default to `output/papers/`.
