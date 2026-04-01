from app2 import create_app, socketio

app2 = create_app()

if __name__ == "__main__":
    socketio.run(app2, debug=True, allow_unsafe_werkzeug=True)
