from fastapi import APIRouter, Request, Depends, Form, Query
from fastapi.responses import HTMLResponse

from authx import TokenPayload

from app.core.auth import auth, get_current_actor_alias_from_cookie, get_payload_from_cookie
from app.core.database import get_db
from app.crud import get_ctrs, get_actor_by_ids, get_senders_register
# Initialize the router and templates
router = APIRouter()
from .main import templates


@router.get("/users/search", response_class=HTMLResponse)
async def search_targets(request: Request, q: str = "", user_ids: list[int] = Query(default=[]), db: Session = Depends(get_db), payload: TokenPayload = Depends(auth.access_token_required)):
    # Query database based on search string
    checked = get_actor_by_ids(user_ids,db)
    ctrs = get_ctrs(db, q)
    available_targets = checked + [ctr for ctr in ctrs if not ctr.id in user_ids]
    
    # Return ONLY the list items for the left column
    return templates.TemplateResponse(
        "forms/select_targets_items.html", 
        {"request": request, "available_targets": available_targets, "checked_targets": user_ids}
    )

@router.get("/record_form_data", response_class=HTMLResponse)
async def record_data(request: Request, info: str, db: Session = Depends(get_db), payload: TokenPayload = Depends(auth.access_token_required)):
    params = dict(request.query_params)

    if info.startswith('senders'):
        senders, sender_alias, flow, ctr_alias = info.split('_')
        senders = get_senders_register(db, flow, params['register'], ctr_alias)
        
        if flow == 'inbound' and not params['register'] in ['cg', 'asr']:
            if sender_alias == "":
                rst = f'<option selected value=""></option>'
            else:
                rst = f'<option value=""></option>'
        else:
            rst = ""

        for sender in senders:
            if sender_alias == sender.alias:
                rst += f'<option "selected" value="{sender.alias}">{sender.alias}</option>'
            else:
                rst += f'<option value="{sender.alias}">{sender.alias}</option>'
        return rst

    return None

"""
@router.get("/users/{target_id}/render-selected", response_class=HTMLResponse)
async def render_selected(request: Request, target_id: int, db: Session = Depends(get_db)):
    target = db.get(Target, target_id)
    
    # Return ONLY the single <li> for the right column
    return templates.TemplateResponse(
        "partials/selected_item.html", 
        {"request": request, "target": target}
    )

@router.get("/users/select-all", response_class=HTMLResponse)
async def select_all(request: Request, q: str = "", db: Session = Depends(get_db)):
    # Find everyone currently matching the search
    statement = select(Target).where(col(Target.alias).contains(q))
    targets = db.exec(statement).all()
    
    # Return all of them as selected fragments
    # HTMX will append these to the right column
    return templates.TemplateResponse(
        "partials/selected_items_batch.html", 
        {"request": request, "targets": targets}
    )

@router.post("/send-email")
async def send_email(user_ids: List[int]):
    # user_ids will arrive in the order they were dragged in the UI!
    # e.g., [4, 1, 9]
    print(f"Sending emails in this order: {user_ids}")
    return HTMLResponse(content="<p>Emails queued successfully!</p>")
"""
