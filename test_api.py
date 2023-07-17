import asyncio

# import websockets
#
# async def message():
# 	async with websockets.connect("ws://127.0.0.1:8001/apiapi/") as socket:
# 		while 1:
#
# 			# await socket.send(msg)
# 			await asyncio.sleep(3)
# 			print(await socket.recv())
#
#
# asyncio.get_event_loop().run_until_complete(message())
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
import base64
with open("publicKey.pem", "rb") as key_file:
    public_key = serialization.load_pem_public_key(
        key_file.read(),
    )


with open("privateKey.pem", "rb") as key_file:
    private_key = serialization.load_pem_private_key(
        key_file.read(),
         password=None,
    )

original_message = 'я люблю Ваню'

b64_message = base64.b64encode(bytes(original_message, 'utf-8'))
print('b64 message', b64_message)
ciphertext = public_key.encrypt(
    b64_message,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)

print('cipher', ciphertext)

plaintext = private_key.decrypt(
    ciphertext,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)

print('plain', plaintext)

currect_message = base64.b64decode(plaintext).decode('utf-8')

print(currect_message)

