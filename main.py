from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from fastapi_babel import _
from fastapi_babel import Babel, BabelConfigs
from fastapi_babel import BabelMiddleware

from sqlmodel import create_engine, SQLModel

from authx import TokenPayload
from authx.exceptions import JWTDecodeError, MissingTokenError, TokenError, RevokedTokenError
from authx_extra.session import SessionMiddleware
#from starlette.middleware.sessions import SessionMiddleware

from app.core.database import init_db # Import the table creation hook
from app.core.auth import auth

from app.routers import router

from app.models import Register, Record, Actor, RecordActor, File, RecordRecord

from app.crud.transfer import transfer_notes, transfer_users, transfer_actors, transfer_registers, transfer_note_user, transfer_tags, transfer_record_tag, transfer_depts, transfer_find_depts, transfer_files, transfer_references


from app.routers.main import templates
from jose import JWTError, jwt
from app.core.config import settings

def locale_selector(request: Request):
    # 1. Try to get the raw cookie that holds your token
    # Adjust "access_token" to whatever your authx cookie name is
    token = request.cookies.get("access_token")
    
    if token:
        try:
            # 2. Manually decode the token (Use your SAME secret key and algorithm)
            # This is what 'get_payload_from_cookie' does behind the scenes
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=["HS256"]
            )
            # 3. Grab the lang from the payload
            return payload.get("lang", "en")
        except Exception as e:
            print(f"Error decoding token in selector: {e}")
            return "ja"
            
    # Fallback if no cookie is found
    return "ja"



babel_configs = BabelConfigs(
    ROOT_DIR=__file__,
    BABEL_DEFAULT_LOCALE="en",
    BABEL_TRANSLATION_DIRECTORY="lang",
)

# Initialize FastAPI
app = FastAPI(title="Sake")

app.add_middleware(
    BabelMiddleware,
    babel_configs=babel_configs,
    jinja2_templates=templates,
    locale_selector=locale_selector,
)

app.add_middleware(
    SessionMiddleware,
    secret_key="my-secret-key",
    http_only=True,
    secure=False,
    max_age=36000,
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
    #transfer_find_depts()
    if False:
        transfer_registers()
        transfer_users()
        transfer_notes()
        transfer_note_user()
        transfer_tags()
        transfer_record_tag()
        transfer_depts()
        transfer_find_depts()
        transfer_files()
        transfer_references()
# Mount Static Files
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# Include Routers
# Use the main router defined in app/routers/main.py
app.include_router(router)

# To run: uvicorn main:app --reload
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
