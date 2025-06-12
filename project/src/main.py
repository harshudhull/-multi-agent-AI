from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any,List
from datetime import datetime
import os
import uuid
import json
import logging

from src.data_extractor import DataExtractor
from src.classifier import ClassifierAgent
from src.memory_manager import MemoryManager
from src.database import init_db, save_extracted_data, get_history
from src.schemas import StoreData, StoreDetails, SaveDatasetRequest, ProfileUpdate

app = FastAPI(title="Multi-Format Intake System")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static + Template Setup
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize Services
data_extractor = DataExtractor()
classifier = ClassifierAgent()
memory_manager = MemoryManager()
init_db()

@app.on_event("startup")
async def startup_event():
    os.makedirs("uploads", exist_ok=True)
    logging.info("System started.")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    history_data = get_history()
    return templates.TemplateResponse("history.html", {"request": request, "history": history_data})

@app.get("/memory", response_class=HTMLResponse)
async def memory_page(request: Request):
    memory_data = memory_manager.get_all_memory()
    return templates.TemplateResponse("memory.html", {"request": request, "memory": memory_data})

@app.post("/api/backend/store-data")
async def store_data_backend(payload: StoreData):
    try:
        data_id = str(uuid.uuid4())
        save_extracted_data(data_id, "backend_json", "json", payload.data, "backend_direct")
        memory_manager.store(data_id, {
            "source": "backend",
            "type": "json",
            "timestamp": datetime.now().isoformat(),
            "data": payload.data
        })
        return {"success": True, "data_id": data_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/backend/store-details")
async def store_details_backend(payload: StoreDetails):
    try:
        details_id = str(uuid.uuid4())
        save_extracted_data(details_id, "processed_details", "details", payload.details, "processed_details")
        return {"success": True, "details_id": details_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/frontend/process-input")
async def process_user_input(file: UploadFile = File(...), input_type: str = Form(...)):
    try:
        allowed_extensions = {'.pdf', '.json', '.txt', '.eml'}
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail="Unsupported file type.")

        safe_filename = os.path.basename(file.filename)
        file_id = str(uuid.uuid4())
        file_path = f"uploads/{file_id}_{safe_filename}"
        with open(file_path, "wb") as f:
            f.write(await file.read())

        classification = classifier.classify(file_path, input_type)
        if input_type.lower() == "file":
            extracted_data = data_extractor.extract_from_file(file_path)
        elif input_type.lower() == "email":
            extracted_data = data_extractor.extract_from_email(file_path)
        elif input_type.lower() == "json":
            extracted_data = data_extractor.extract_from_json(file_path)
        else:
            raise HTTPException(status_code=400, detail="Invalid input type.")

        memory_manager.store(file_id, {
            "filename": safe_filename,
            "type": input_type,
            "classification": classification,
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "extracted_data": extracted_data
        })

        return {
            "success": True,
            "file_id": file_id,
            "filename": safe_filename,
            "classification": classification,
            "extracted_data": extracted_data,
            "file_path": file_path
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/extract/{file_id}", response_class=HTMLResponse)
async def get_extraction_page(request: Request, file_id: str):
    try:
        memory_data = memory_manager.get(file_id)
        if not memory_data:
            raise HTTPException(status_code=404, detail="Not found")

        extracted_data = memory_data.get("extracted_data")
        if not extracted_data:
            input_type = memory_data.get("type")
            file_path = memory_data.get("file_path")
            if input_type.lower() == "file":
                extracted_data = data_extractor.extract_from_file(file_path)
            elif input_type.lower() == "email":
                extracted_data = data_extractor.extract_from_email(file_path)
            elif input_type.lower() == "json":
                extracted_data = data_extractor.extract_from_json(file_path)

        classification = memory_data.get("classification", {})
        if isinstance(classification, str):
            try:
                classification = json.loads(classification)
            except:
                classification = {}

        return templates.TemplateResponse("extract.html", {
            "request": request,
            "file_id": file_id,
            "filename": memory_data.get("filename"),
            "extracted_data": json.dumps(extracted_data, indent=2),
            "file_path": memory_data.get("file_path"),
            "classification": classification.get("intent", "Unknown")
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/api/save-dataset")
async def save_to_dataset(payload: SaveDatasetRequest):
    try:
        file_id = payload.file_id
        memory_data = memory_manager.get(file_id)
        if not memory_data:
            raise HTTPException(status_code=404, detail="File not found")

        save_extracted_data(
            data_id=file_id,
            original_filename=memory_data.get("filename"),
            file_type=memory_data.get("type"),
            extracted_data=payload.extracted_data,
            classification=memory_data.get("classification", {}).get("intent", "Unknown")
        )

        # Removed store_data_backend() to avoid recursion
        return {"success": True, "message": "Saved to dataset."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Save failed: {str(e)}")

@app.get("/api/user/profile")
async def get_user_profile():
    return {"username": "Admin User", "email": "admin@example.com", "role": "Administrator"}

@app.put("/api/user/profile")
async def update_user_profile(profile_data: ProfileUpdate):
    return {"success": True, "message": "Profile updated successfully"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
