from pathlib import Path

path = Path("app\main.py")
text = path.read_text(encoding="utf-8")

if "from app.realtime import router as realtime_router" not in text:
    text = "from app.realtime import router as realtime_router`n" + text

if "app.include_router(realtime_router)" not in text:
    marker = "app = FastAPI("
    start = text.find(marker)

    if start == -1:
        raise SystemExit("Could not find FastAPI app declaration.")

    line_end = text.find("`n", start)
    if line_end == -1:
        line_end = text.find("`r`n", start)

    if line_end == -1:
        raise SystemExit("Could not locate FastAPI declaration line.")

    line_end += 2
    text = text[:line_end] + "`napp.include_router(realtime_router)`n" + text[line_end:]

path.write_text(text, encoding="utf-8")
print("SSE router connected successfully.")
