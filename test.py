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
        # received_size = 0
        # buf_size = 10000
        # full_size = os.path.getsize("017-4852450_5920950975.pdf")
        # print('full_size', full_size)
        # time.sleep(1)
        # while received_size < full_size:
        #     time.sleep(1)
        #
        #     with open('017-4852450_5920950975.pdf', 'rb') as file:
        #         file.seek(received_size)
        #         file = base64.b64encode(file.read(buf_size)).decode('UTF-8')
        #     received_size += buf_size
        #     # file = base64.b64encode(open('017-4852450_5920950975.pdf', 'r', encoding='utf-8').read()).decode('UTF-8')
        #     print(received_size)
        #     ws.send(json.dumps({'event': "outgoing", 'action': "upload", 'upload_data': {"content": file}}))
        # print('отправили что ли все?')

        ws.close()
        print("thread terminating...")
    _thread.start_new_thread(run, ())

if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://pashtonp.space/client/",
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
    ws.run_forever()