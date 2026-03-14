from fastapi import APIRouter, Depends, HTTPException, status # pyre-ignore[21]
from sqlalchemy.orm import Session # pyre-ignore[21]
from app.core.database import get_db # pyre-ignore[21]
from app.models import ApiKey # pyre-ignore[21]
from app.api.auth import get_me # pyre-ignore[21]
from app.services.key_encryption import KeyEncryptionService # pyre-ignore[21]
from pydantic import BaseModel # pyre-ignore[21]
import aiohttp # pyre-ignore[21]

router = APIRouter()

class KeySubmit(BaseModel):
    service: str
    key: str

class KeyTest(BaseModel):
    service: str
    key: str

@router.get("/")
def get_keys(user = Depends(get_me), db: Session = Depends(get_db)):
    keys = db.query(ApiKey).filter(ApiKey.user_id == user.id).all()
    # Return only the service name for security
    return [{"service": k.service, "id": k.id} for k in keys]

@router.post("/")
def save_key(key_in: KeySubmit, user = Depends(get_me), db: Session = Depends(get_db)):
    # Check if key already exists for service
    existing = db.query(ApiKey).filter(ApiKey.user_id == user.id, ApiKey.service == key_in.service).first()
    
    encrypted = KeyEncryptionService.encrypt(key_in.key)
    
    if existing:
        existing.encrypted_key = encrypted
    else:
        new_key = ApiKey(user_id=user.id, service=key_in.service, encrypted_key=encrypted)
        db.add(new_key)
    
    db.commit()
    return {"status": "saved"}

@router.post("/test")
async def test_key(test_in: KeyTest):
    """Minimal test call to verify API key validity."""
    if test_in.service == "hf":
        url = "https://api-inference.huggingface.co/models/gpt2"
        headers = {"Authorization": f"Bearer {test_in.key}"}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json={"inputs": "Hello"}) as resp:
                if resp.status == 200:
                    return {"valid": True}
                else:
                    return {"valid": False, "error": await resp.text()}
    
    elif test_in.service == "groq":
        # Groq doesn't have a simple health endpoint that is free, so we do a tiny completion
        url = "https://api.groq.com/openai/v1/models"
        headers = {"Authorization": f"Bearer {test_in.key}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    return {"valid": True}
                else:
                    return {"valid": False, "error": "Invalid API Key"}
                    
    return {"valid": False, "error": "Unsupported service for testing"}

@router.delete("/{service}")
def delete_key(service: str, user = Depends(get_me), db: Session = Depends(get_db)):
    key = db.query(ApiKey).filter(ApiKey.user_id == user.id, ApiKey.service == service).first()
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    db.delete(key)
    db.commit()
    return {"status": "deleted"}
