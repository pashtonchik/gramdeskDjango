import _thread
import base64
import json
import os
import time

import websocket


def on_message(ws, message):
    print(11)
def on_error(ws, error):
    print(2)
def on_close(ws, close_status_code, close_msg):
    print("### closed ###")
def on_open(ws):
    def run(*args):

        print(11111)
        time.sleep(2)
        received_size = 0
        len1 = 0
        buf_size = 50000
        full_size = os.path.getsize("WIN_20210621_12_33_56_Pro.jpg")
        print('full_size', full_size)
        time.sleep(1)
        data = ''
        while received_size < full_size:
            time.sleep(1)

            with open('WIN_20210621_12_33_56_Pro.jpg', 'rb') as file:
                print('весь', base64.b64encode(file.read()).decode('UTF-8'))
                file.seek(0, 0)
                print('весь в байтах', file.read(10))
                # if received_size != 0:
                file.seek(received_size, 0)
                bytes = file.read(buf_size)
                print('эти байты', bytes)
                file = base64.b64encode(bytes).decode('UTF-8')
                print(file)
            received_size += buf_size
            len1 += len(file)
            data += file
            # file = base64.b64encode(open('017-4852450_5920950975.pdf', 'r', encoding='utf-8').read()).decode('UTF-8')
            print(received_size)
            ws.send(json.dumps({'event': "outgoing", 'action': "upload", 'upload_data': {"content": file, "id": "90"}}))

        with open('127.pdf', 'ab+') as file:
            file.write(base64.b64decode(data))
        print('отправили что ли все?')
        print(len1)
        ws.close()
        print("thread terminating...")


    _thread.start_new_thread(run, ())

if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://pashtonp.space/upload/",
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
    ws.run_forever()