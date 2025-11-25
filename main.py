import base64
import json
from fastapi import FastAPI, HTTPException
from io import BytesIO
import pandas as pd
import docx

app = FastAPI()

# ---------- File converters ----------
def excel_to_text(content: bytes) -> str:
    df = pd.read_excel(BytesIO(content))
    return df.to_csv(index=False)

def csv_to_text(content: bytes) -> str:
    return content.decode(errors="ignore")

def json_to_text(content: bytes) -> str:
    obj = json.loads(content.decode(errors="ignore"))
    return json.dumps(obj, indent=2, ensure_ascii=False)

def docx_to_text(content: bytes) -> str:
    document = docx.Document(BytesIO(content))
    return "\n".join(p.text for p in document.paragraphs)


@app.post("/file-to-text")
async def file_to_text(body: dict):
    # --------------------------
    # Detect which schema is used
    # --------------------------
    if "contentBytes" in body:  # Schema 1
        file_b64 = body["contentBytes"]
        filename = body.get("name", "file")
    elif "Content" in body and "Name" in body:  # Schema 2
        file_b64 = body.get("Content") or body.get("Value")
        filename = body["Name"]
    else:
        raise HTTPException(status_code=400, detail="Invalid schema. Missing contentBytes or Content/Name.")

    # Decode base64
    try:
        content = base64.b64decode(file_b64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 content")

    # Detect extension
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    # Convert
    try:
        if ext in {"xlsx", "xls"}:
            text = excel_to_text(content)
        elif ext == "csv":
            text = csv_to_text(content)
        elif ext == "json":
            text = json_to_text(content)
        elif ext == "docx":
            text = docx_to_text(content)
        else:
            text = content.decode(errors="ignore")
    except Exception as ex:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {ex}")

    return {
        "filename": filename,
        "extension": ext,
        "text": text
    }