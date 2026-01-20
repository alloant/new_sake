from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from sqlmodel import create_engine, SQLModel

from authx.exceptions import JWTDecodeError, MissingTokenError, TokenError, RevokedTokenError
from authx_extra.session import SessionMiddleware

from app.core.database import init_db # Import the table creation hook
from app.core.auth import auth

from app.routers import router

from app.models import Register, Record, Actor, User, RecordUser, File, RecordRecord

from app.crud.transfer import transfer_notes, transfer_users, transfer_actors, transfer_registers, transfer_contacts, transfer_ctrs, transfer_note_user, transfer_tags, transfer_record_tag, transfer_depts, transfer_find_depts, transfer_files, transfer_references

# Initialize FastAPI
app = FastAPI(title="Sake")
app.add_middleware(
    SessionMiddleware,
    secret_key="my-secret-key",
    http_only=True,
    secure=False,
    max_age=0,
    session_cookie="sid",
    session_object="session",
)

auth.handle_errors(app)

@app.exception_handler(401)
@app.exception_handler(TokenError)
@app.exception_handler(RevokedTokenError)
@app.exception_handler(JWTDecodeError)
@app.exception_handler(MissingTokenError)
async def auth_exception_handler(request: Request, exc: Exception):
    return RedirectResponse(url="/login")

@app.on_event("startup")
def on_startup():
    # This creates all tables when the app first starts
    init_db()
    if False:
        transfer_registers()
        transfer_actors()
        transfer_users()
        transfer_contacts()
        transfer_ctrs()
        transfer_notes()
        transfer_note_user()
        transfer_tags()
        transfer_record_tag()
        transfer_depts()
        transfer_find_depts()
        transfer_files()
        transfer_references()
# Mount Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include Routers
# Use the main router defined in app/routers/main.py
app.include_router(router)

# To run: uvicorn main:app --reload
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


