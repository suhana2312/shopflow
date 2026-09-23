from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from app.core.security import decode_access_token
from app.core.database import SessionLocal
from app.models.orders import Order
from app.models.user import User, UserRole
from app.websocket.connection_manager import ws_manager
from app.core.logging import logger

router = APIRouter()

@router.websocket("/ws/orders/{order_id}")
async def order_websocket_endpoint(
    websocket: WebSocket,
    order_id: str,
    token: str = Query(..., description="JWT Bearer access token")
):
    # 1. Authenticate JWT token
    payload = decode_access_token(token)
    if not payload:
        logger.warning(f"WebSocket connection rejected: invalid or expired token for order {order_id}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = payload.get("sub")
    user_role = payload.get("role")

    # 2. Check Order Existence and Ownership
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            logger.warning(f"WebSocket connection rejected: order {order_id} not found")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Security check: User A cannot listen to User B's order unless user is ADMIN
        if order.user_id != user_id and user_role != UserRole.ADMIN.value:
            logger.warning(f"WebSocket security violation: user {user_id} attempted to subscribe to order {order_id} owned by {order.user_id}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # 3. Accept connection
        await ws_manager.connect(order_id, websocket)

        # Send initial status payload immediately upon connection
        await websocket.send_json({
            "order_id": order.id,
            "order_number": order.order_number,
            "status": order.status.value,
            "total_amount": str(order.total_amount),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "message": f"Connected to live updates for order {order.order_number}"
        })

        # Keep connection open and handle incoming ping / client messages
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        ws_manager.disconnect(order_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket unexpected error on order {order_id}: {e}")
        ws_manager.disconnect(order_id, websocket)
    finally:
        db.close()
