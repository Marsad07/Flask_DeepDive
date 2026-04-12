from app2 import create_app, socketio

app2 = create_app()

if __name__ == "__main__":
    socketio.run(app2, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)