from flask_socketio import SocketIO

# Initialize SocketIO without the app object initially.
# It will be initialized with the app in app.py using socketio.init_app(app).
# cors_allowed_origins can be set here or during init_app.
socketio = SocketIO(cors_allowed_origins="*")

