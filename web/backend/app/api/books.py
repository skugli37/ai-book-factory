from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks # pyre-ignore[21]
from sqlalchemy.orm import Session # pyre-ignore[21]
from app.core.database import get_db # pyre-ignore[21]
from app.models import Book, User # pyre-ignore[21]
from app.api.auth import get_me # pyre-ignore[21]
from app.services.book_generator import WebBookFactory # pyre-ignore[21]
from app.services.key_encryption import KeyEncryptionService # pyre-ignore[21]
from app.models import ApiKey # pyre-ignore[21]
from config import BookConfig # pyre-ignore[21]
from pydantic import BaseModel # pyre-ignore[21]
import uuid
import asyncio

router = APIRouter()

class BookCreate(BaseModel):
    title: str
    topic: str
    genre: str
    chapters: int = 5

@router.get("/")
def list_books(user: User = Depends(get_me), db: Session = Depends(get_db)):
    # get_me returns a User object
    return db.query(Book).filter(Book.user_id == user.id).all()

@router.get("/stats")
def get_stats(user: User = Depends(get_me), db: Session = Depends(get_db)):
    from sqlalchemy.sql import func # pyre-ignore[21]
    total_books = db.query(Book).filter(Book.user_id == user.id).count()
    completed_books = db.query(Book).filter(Book.user_id == user.id, Book.status == "completed").count()
    
    # Real sum of word counts from the database
    total_words_row = db.query(func.sum(Book.word_count)).filter(Book.user_id == user.id).first()
    total_words = total_words_row[0] if total_words_row and total_words_row[0] else 0
    
    return {
        "total_books": total_books,
        "completed_books": completed_books,
        "total_words": total_words
    }

@router.post("/")
def create_book(
    book_in: BookCreate, 
    background_tasks: BackgroundTasks,
    user: User = Depends(get_me), 
    db: Session = Depends(get_db)
):
    job_id = str(uuid.uuid4())
    # Use topic as initial title if none provided
    initial_title = book_in.title if book_in.title and book_in.title != "New AI Book" else book_in.topic
    
    new_book = Book(
        user_id=user.id,
        title=initial_title,
        topic=book_in.topic,
        genre=book_in.genre,
        status="pending"
    )
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    
    # Trigger background task
    background_tasks.add_task(run_generation_job, new_book.id, user.id, book_in, job_id)
    
    return {"status": "accepted", "book_id": new_book.id, "job_id": job_id}

async def run_generation_job(book_id: int, user_id: int, book_in: BookCreate, job_id: str):
    import asyncio
    await asyncio.sleep(2)  # Give WebSocket time to connect
    print(f"DEBUG: run_generation_job started for job_id={job_id}")
    # Get DB session
    from app.core.database import SessionLocal # pyre-ignore[21]
    db = SessionLocal()
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        print(f"DEBUG: Found book in DB. title={book.title}")
        # Get Groq Key for User
        key_obj = db.query(ApiKey).filter(ApiKey.user_id == user_id, ApiKey.service == 'groq').first()
        if key_obj:
            api_key = KeyEncryptionService.decrypt(key_obj.encrypted_key)
        else:
            from config import GROQ_API_KEY # pyre-ignore[21]
            api_key = GROQ_API_KEY
        
        if not api_key:
            from app.websocket.manager import manager # pyre-ignore[21]
            await manager.send_update(job_id, {
                "stage": "failed",
                "percent": 0,
                "latest_text": "No Groq API key found. Please add your Groq API key in Settings."
            })
            book.status = "failed"
            db.commit()
            return

        factory = WebBookFactory(job_id, api_key=api_key)
        
        config = BookConfig(
            title=book_in.topic,
            genre=book_in.genre,
            target_words=20000,
            chapters=book_in.chapters,
            topic=book_in.topic
        )
        
        await factory.generate_web_book(config, db, book)
    except Exception as e:
        import traceback
        with open("/tmp/backend_err.txt", "w") as f:
            f.write(traceback.format_exc())
        
        from app.websocket.manager import manager # pyre-ignore[21]
        await manager.send_update(job_id, {
            "stage": "failed",
            "percent": 0,
            "latest_text": f"Generation failed: {str(e)}"
        })
        book.status = "failed"
        db.commit()
    finally:
        db.close()

@router.delete("/{book_id}")
def delete_book(book_id: int, user: User = Depends(get_me), db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id, Book.user_id == user.id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(book)
    db.commit()
    return {"status": "deleted"}
