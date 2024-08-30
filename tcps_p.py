import io
import socket
import struct
import threading
from flask import Flask, Response, render_template_string
import cv2
import numpy as np

app = Flask(__name__)


current_frame = None

def get_frame():
    global current_frame
    if current_frame is None:
        return None
    return current_frame

@app.route('/')
def index():
    return render_template_string('''
        <html>
        <body>
            <h1>Live Video Feed</h1>
            <img src="/video_feed" style="width: auto; height: auto;">
        </body>
        </html>
    ''')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def generate_frames():
    while True:
        frame = get_frame()
        if frame is None:
            continue
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def socket_thread():
    while True:
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind(('0.0.0.0', 21580))  # یا پورت دیگری که می‌خواهید استفاده کنید
            server_socket.listen(1)
            print("Server is listening on port 21580...")
            connection = server_socket.accept()[0].makefile('rb')
            print("Client connected")
            
            while True:
                try:
                    image_len = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
                    if not image_len:
                        break
                    image_stream = io.BytesIO()
                    image_stream.write(connection.read(image_len))
                    image_stream.seek(0)
                    image_data = np.frombuffer(image_stream.getvalue(), dtype=np.uint8)
                    global current_frame
                    current_frame = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
                except (ConnectionResetError, BrokenPipeError):
                    print("Connection lost with client")
                    break
                
        except Exception as e:
            print(f"Error in socket handling: {e}")
        finally:
            connection.close()
            server_socket.close()

if __name__ == '__main__':
    threading.Thread(target=socket_thread, daemon=True).start()
    app.run(host='0.0.0.0', port=21581)
