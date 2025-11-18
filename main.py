import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Event, Message, Membership

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utility to convert Mongo docs

def serialize_doc(doc):
    if not doc:
        return doc
    doc["id"] = str(doc.get("_id"))
    doc.pop("_id", None)
    return doc


@app.get("/")
def read_root():
    return {"message": "Events + Chat API"}


@app.get("/events", response_model=List[dict])
def list_events(lat: Optional[float] = None, lng: Optional[float] = None, radius_km: float = 10):
    """
    Return events; if lat/lng provided, return within radius_km (simple bbox filter for demo).
    """
    query = {}
    if lat is not None and lng is not None:
        # Simple bounding box ~ not precise but fine for demo
        delta = radius_km / 111.0  # approx degrees per km
        query = {
            "lat": {"$gte": lat - delta, "$lte": lat + delta},
            "lng": {"$gte": lng - delta, "$lte": lng + delta},
        }
    docs = db["event"].find(query).limit(200)
    return [serialize_doc(d) for d in docs]


@app.post("/events", status_code=201)
def create_event(event: Event):
    event_id = create_document("event", event)
    return {"id": event_id}


class JoinRequest(BaseModel):
    user: str


@app.post("/events/{event_id}/join")
def join_event(event_id: str, body: JoinRequest):
    # Validate event exists
    try:
        doc = db["event"].find_one({"_id": ObjectId(event_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid event id")
    if not doc:
        raise HTTPException(status_code=404, detail="Event not found")

    # Upsert membership
    db["membership"].update_one(
        {"event_id": event_id, "user": body.user},
        {"$set": {"event_id": event_id, "user": body.user}},
        upsert=True,
    )
    # Increment attendees count
    db["event"].update_one({"_id": ObjectId(event_id)}, {"$inc": {"attendees": 1}})
    return {"ok": True}


@app.get("/events/{event_id}/messages")
def get_messages(event_id: str, limit: int = 50):
    msgs = db["message"].find({"event_id": event_id}).sort("created_at", -1).limit(limit)
    return [serialize_doc(m) for m in msgs][::-1]


class SendMessage(BaseModel):
    user: str
    text: str


@app.post("/events/{event_id}/messages")
def send_message(event_id: str, body: SendMessage):
    # Ensure member exists (optional; allow anyone who joined)
    member = db["membership"].find_one({"event_id": event_id, "user": body.user})
    if not member:
        raise HTTPException(status_code=403, detail="Join the event to chat")
    msg = Message(event_id=event_id, user=body.user, text=body.text)
    msg_id = create_document("message", msg)
    return {"id": msg_id}


@app.get("/test")
def test_database():
    info = {"backend": "ok"}
    try:
        info["db"] = "ok" if db is not None else "not-configured"
        info["collections"] = db.list_collection_names() if db is not None else []
    except Exception as e:
        info["error"] = str(e)
    return info


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
