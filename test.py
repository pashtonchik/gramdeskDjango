import _thread
import base64
import json
import os
import time

import websocket


def on_message(ws, message):
    if message != '{"ok": true}':
        data = json.loads(message)
        received_bytes = data['content']
        received_bytes = base64.b64decode(received_bytes.encode('UTF-8'))

        with open('123.pdf', mode='ab+') as f:
            f.write(received_bytes)


def on_error(ws, error):
    print(2)
def on_close(ws, close_status_code, close_msg):
    print("### closed ###")
def on_open(ws):
    def run(*args):

        print(11111)
        # time.sleep(2)
        # received_size = 0
        # len1 = 0
        # buf_size = 1000000
        # full_size = os.path.getsize("cmake-3.27.6-windows-x86_64.msi")
        # print('full_size', full_size)
        # time.sleep(1)
        # data = ''
        received = 0

        while True:
            time.sleep(2)

            ws.send(json.dumps({'event': "outgoing", 'action': "get_attachment", 'attachment': {"received_bytes": received, "id": "659"}}))
            received += 10000
            print(111)


        print('отправили что ли все?')
        print(len1)
        ws.close()
        print("thread terminating...")


    _thread.start_new_thread(run, ())

if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://185.138.164.171:8000/download/",
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
    ws.run_forever()