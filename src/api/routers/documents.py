from fastapi import APIRouter, HTTPException
from pathlib import Path

router = APIRouter(prefix="/documents", tags=["Documents"])

REPORTS_DIR = Path("reports")


@router.get("")
def list_documents():

    if not REPORTS_DIR.exists():
        return {
            "count": 0,
            "documents": []
        }

    files = []

    for file in REPORTS_DIR.iterdir():
        if file.is_file():
            files.append({
                "name": file.name,
                "path": str(file),
                "size_bytes": file.stat().st_size
            })

    return {
        "count": len(files),
        "documents": files
    }


@router.get("/{filename}")
def get_document(filename: str):

    file_path = REPORTS_DIR / filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return {
        "name": file_path.name,
        "path": str(file_path),
        "size_bytes": file_path.stat().st_size
    }
