from fastapi import FastAPI, WebSocket, WebSocketDisconnect, APIRouter, Depends, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.concurrency import run_in_threadpool

from authx import TokenPayload

from app.core.redis_bus import broadcast
from app.core.auth import auth
from app.core.database import get_db

from app.crud import get_actor_by_alias

import asyncio

router = APIRouter()


@router.websocket("/ws/{actor_alias}")
async def websocket_endpoint(websocket: WebSocket, actor_alias: str, db: Session = Depends(get_db)):
    await websocket.accept()
    #current_actor = get_actor_by_alias(db,actor_alias)
    current_actor = await run_in_threadpool(get_actor_by_alias, db, actor_alias)
    
    # Define the channels we want to listen to
    channels = [f'actor_{current_actor.alias}', f'role_{current_actor.role}']

    async def listen_to_channel(channel_name: str):
        try:
            async with broadcast.subscribe(channel=channel_name) as subscriber:
                async for event in subscriber:
                    await websocket.send_text(event.message)
        except Exception as e:
            print(f"DEBUG: Listener Error: {e}")

    # 2. Receiver to detect when the user disconnects
    async def message_receiver():
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            # Triggered when the user leaves/refreshes
            raise 

    # 3. Create a list of tasks
    # Generate one sender task per channel
    sender_tasks = [asyncio.create_task(listen_to_channel(ch)) for ch in channels]
    receiver_task = asyncio.create_task(message_receiver())
    
    # Combine them all into one list
    all_tasks = sender_tasks + [receiver_task]

    try:
        # Wait for ANY task to finish (e.g., receiver raises WebSocketDisconnect)
        done, pending = await asyncio.wait(
            all_tasks,
            return_when=asyncio.FIRST_COMPLETED,
        )
    except Exception as e:
        print(f"Socket Task Error: {e}")
    finally:
        # CLEANUP: Cancel everything still running to unblock the server
        for task in all_tasks:
            if not task.done():
                task.cancel()
        
        # This is the magic line that unblocks the "Reloading..." process
        await asyncio.gather(*all_tasks, return_exceptions=True)


async def broadcast_channels(channels: list[str], actor_alias: str, msg: str = ""):
    message = f"{actor_alias}|{msg}"
    trigger_html = f'<div id="sock_id" hx-swap-oob="true"><span hx-get="/socket-updated?message={message}" hx-trigger="load" hx-swap="outerHTML"></span></div>'

    for channel in channels:
        await broadcast.publish(channel=channel, message=trigger_html)


@router.get("/socket-updated", response_class=HTMLResponse)
async def socket_updated(
    message: str, 
    response: Response,
    payload: TokenPayload = Depends(auth.access_token_required)
):
    try:
        actor_alias, content = message.split('|')
    except ValueError:
        return "<span>Invalid message format</span>"

    # For now, let's just return the notification trigger
    notification = f"'{content}'"

    # Set the HTMX Trigger header
    response.headers['HX-Trigger'] = 'socket-updated'

    if payload.alias == actor_alias:
        return ''

    return f'<span hx-on:htmx:load="sendNotification({notification})" hx-trigger="load"></span>'


"""
import redis
async def check_redis():
    # Connect to Redis
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)

    # Get all active channels
    active_channels = r.pubsub_channels()
    print(f"Active channels: {active_channels}")
"""
