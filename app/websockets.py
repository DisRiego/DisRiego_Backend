from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import json
import asyncio

class NotificationManager:
    """Clase que gestiona las conexiones WebSocket para las notificaciones"""
    
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.connection_ids: Dict[WebSocket, int] = {}
        
    async def connect(self, websocket: WebSocket, user_id: int):
        """Establecer conexión con un cliente WebSocket"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        self.connection_ids[websocket] = user_id
        
    def disconnect(self, websocket: WebSocket):
        """Desconectar un cliente WebSocket"""
        user_id = self.connection_ids.get(websocket)
        if user_id:
            if user_id in self.active_connections:
                self.active_connections[user_id].remove(websocket)
                # Si no quedan conexiones para este usuario, eliminamos la entrada
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            # Eliminar la referencia al websocket en connection_ids
            del self.connection_ids[websocket]
    
    async def send_notification(self, user_id: int, message: dict):
        """Enviar una notificación a un usuario específico"""
        if user_id in self.active_connections:
            disconnected_websockets = []
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_json(message)
                except WebSocketDisconnect:
                    disconnected_websockets.append(websocket)
                except Exception as e:
                    print(f"Error enviando mensaje a WebSocket: {str(e)}")
                    disconnected_websockets.append(websocket)
            
            # Eliminar las conexiones desconectadas
            for websocket in disconnected_websockets:
                self.disconnect(websocket)
                
    async def broadcast(self, message: dict):
        """Enviar una notificación a todos los usuarios conectados"""
        disconnected_websockets = []
        for user_id, connections in self.active_connections.items():
            for websocket in connections:
                try:
                    await websocket.send_json(message)
                except WebSocketDisconnect:
                    disconnected_websockets.append(websocket)
                except Exception as e:
                    print(f"Error enviando mensaje a WebSocket: {str(e)}")
                    disconnected_websockets.append(websocket)
        
        # Eliminar las conexiones desconectadas
        for websocket in disconnected_websockets:
            self.disconnect(websocket)


# Instancia global del gestor de notificaciones
notification_manager = NotificationManager()