from fastapi import FastAPI, WebSocket, WebSocketDisconnect, APIRouter, Depends
from fastapi.responses import HTMLResponse

from authx import TokenPayload

from broadcaster import Broadcast

from app.core.auth import auth

import asyncio

router = APIRouter()
# 1. Initialize Broadcast with your Redis URL
# In production, use an environment variable for the URL
broadcast = Broadcast("redis://localhost:6379")
app = FastAPI(on_startup=[broadcast.connect], on_shutdown=[broadcast.disconnect])

@router.websocket("/ws/{channel_name}")
async def websocket_endpoint(websocket: WebSocket, channel_name: str):
    await websocket.accept()
    
    # We use actor_{channel_name} to match your connection logic
    async with broadcast.subscribe(channel=f'actor_{channel_name}') as subscriber:
        async def message_sender():
            try:
                async for event in subscriber:
                    await websocket.send_text(event.message)
            except asyncio.CancelledError:
                # This happens when the receiver stops and cancels this task
                return

        async def message_receiver():
            try:
                while True:
                    await websocket.receive_text()
            except WebSocketDisconnect:
                # When the user refreshes/leaves, this triggers
                raise 

        # Create the tasks
        sender_task = asyncio.create_task(message_sender())
        receiver_task = asyncio.create_task(message_receiver())

        try:
            # Wait for either to finish. If one dies, we kill the other.
            done, pending = await asyncio.wait(
                [sender_task, receiver_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
        except Exception as e:
            print(f"Socket Task Error: {e}")
        finally:
            # CLEANUP: Cancel anything still running to unblock the server
            for task in [sender_task, receiver_task]:
                if not task.done():
                    task.cancel()
            
            # This is the magic line that unblocks the "Reloading..." process
            await asyncio.gather(*[sender_task, receiver_task], return_exceptions=True)

async def broadcast_all_channels(actor_alias: str, role: str, msg: str = ""):
    # We send the HTMX trigger snippet directly into the Redis pipe
    message = f"{actor_alias}|msg"
    trigger_html = f'<div id="sock_id"><span hx-get="/socket-updated?message={message}" hx-trigger="load" hx-swap="outerHTML"></span></div>'
    await broadcast.publish(channel=f"actor_{role}", message=trigger_html)


@router.get("/socket-updated", response_class=HTMLResponse)
async def socket_updated(request: Request, message: str, payload: TokenPayload = Depends(auth.access_token_required)):
    actor_alias, content = message.split('|')
    if actor_alias != payload.alias and content:
        notification = f"'{content}'"
        response = make_response(f'<span hx-on:htmx:load="sendNotification({notification})" hx-trigger="load"></span>')
    else:
        response = make_response(f'<span></span>')

    response.headers['HX-Trigger'] = 'socket-updated'
    
    return response

"""
import redis
async def check_redis():
    # Connect to Redis
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)

    # Get all active channels
    active_channels = r.pubsub_channels()
    print(f"Active channels: {active_channels}")
"""
