import subprocess
import uuid
import os
import re
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
UPLOAD_DIR = Path("/tmp/dpi_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_SIZE_MB = 5

@app.get("/", response_class=HTMLResponse)
def home():
    return Path("web/static/index.html").read_text()

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    # Basic validation — reject anything that isn't a real pcap
    header = await file.read(4)
    if header != b"\xd4\xc3\xb2\xa1" and header != b"\xa1\xb2\xc3\xd4":
        raise HTTPException(400, "Not a valid PCAP file")
    await file.seek(0)

    contents = await file.read()
    if len(contents) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {MAX_SIZE_MB}MB limit")

    job_id = str(uuid.uuid4())
    in_path = UPLOAD_DIR / f"{job_id}_in.pcap"
    out_path = UPLOAD_DIR / f"{job_id}_out.pcap"
    in_path.write_bytes(contents)

    try:
        result = subprocess.run(
            ["./dpi_engine", str(in_path), str(out_path)],
            capture_output=True, text=True, timeout=15
        )
    finally:
        in_path.unlink(missing_ok=True)
        out_path.unlink(missing_ok=True)

    return JSONResponse({"report": result.stdout or result.stderr})

@app.post("/analyze-sample")
def analyze_sample():
    result = subprocess.run(
        ["./dpi_engine", "test_dpi.pcap", "/tmp/sample_out.pcap"],
        capture_output=True, text=True, timeout=15
    )
    return JSONResponse({"report": result.stdout or result.stderr})
