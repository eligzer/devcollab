from flask_socketio import SocketIO

socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="threading",
    logger=True,
    engineio_logger=True
)