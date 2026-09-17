import io
import uuid
import zipfile
from datetime import date
from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import db, storage
from polaroid import compose_polaroid, resize_photo

app = FastAPI(title="Instabox API")

class EventCreate(BaseModel):
    client_name: str
    event_type: str
    event_date: date

class EventCreateResponse(BaseModel):
    event_id: str

@app.post("/events", response_model=EventCreateResponse)
def create_event(payload: EventCreate):
    event_id = db.create_event(
        client_name=payload.client_name,
        event_type=payload.event_type,
        event_date=payload.event_date,
    )
    return {"event_id": event_id}

@app.post("/upload")
async def upload_photo(event_id: str = Form(...), message: str = Form(""), file: UploadFile = None):
    event = db.get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="event_id no existe")
    if file is None:
        raise HTTPException(status_code=400, detail="falta el archivo 'file'")

    raw_bytes = await file.read()

    # resize a 128x128
    thumb_bytes = resize_photo(raw_bytes)
    original_key = f"{uuid.uuid4()}.jpg"
    storage.save_original(original_key, thumb_bytes)

    # componer en formato polaroid
    polaroid_bytes = compose_polaroid(thumb_bytes, message)
    polaroid_key = f"{uuid.uuid4()}.jpg"
    storage.save_polaroid(polaroid_key, polaroid_bytes)

    photo_id = db.add_photo(event_id, original_key, polaroid_key, message)

    return {
        "photo_id": photo_id,
        "original_key": original_key,
        "polaroid_key": polaroid_key,
    }


@app.get("/events/{event_id}")
def get_event(event_id: str):
    event = db.get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="event_id no existe")
    return {**event, "photo_count": db.count_photos(event_id)}


@app.post("/finish")
def finish_event(event_id: str = Form(...)):
    event = db.get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="event_id no existe")

    photos = db.get_photos(event_id)
    if not photos:
        raise HTTPException(status_code=400, detail="el evento no tiene fotos todavía")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for photo in photos:
            data = storage.read_polaroid(photo["polaroid_key"])
            zf.writestr(photo["polaroid_key"], data)
    zip_buffer.seek(0)

    filename = f"evento_{event_id}.zip"
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
