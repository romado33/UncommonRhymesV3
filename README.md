# UncommonRhymesV3

Fresh rebuild with predictable DB handling, strict schema, and CI.  
- Dev DBs (tiny) live in repo.  
- Full DBs come from GitHub Releases (download + checksum).  
- Private rap DB is local-only (not committed).

## Quick start
\\\ash
python -m venv .venv && . .venv/Scripts/Activate.ps1  # Windows
pip install -r requirements.txt
python app.py
\\\

## Env
- \UR_RAP_DB\ â†’ your local private rap DB (e.g., C:\Users\RobDods\Downloads\patterns.db)
- \UR_USE_FULL_DB=1\ â†’ pull release DBs into data/cache/
- \UR_UNCOMMON_ZIPF_MAX=4.0\ (default)
- \OPENAI_API_KEY\ (optional LLM features)
