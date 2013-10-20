import base64
import config
from Crypto.Cipher import AES

PADDING = "0123456789abcdef"

def encrypt(message):
    OBJ = AES.new(config.SECRET_KEY, AES.MODE_CBC, config.IV)
    numToPad = 16 - ( len(message) + 4 ) % 16
    paddedMessage = "%04d%s%s" % (len(message),message,PADDING[:numToPad])
    encryptedMessage = OBJ.encrypt(paddedMessage)
    b64Message = base64.b64encode(encryptedMessage)
    return(b64Message)

def decrypt(b64Message):
    OBJ = AES.new(config.SECRET_KEY, AES.MODE_CBC, config.IV)
    message = base64.b64decode(b64Message)
    paddedMessage = OBJ.decrypt(message)
    messageLen = int(paddedMessage[:4])
    numToPad = 16 - ( messageLen + 4 ) % 16
    message = paddedMessage[4:messageLen+4]
    if (paddedMessage[messageLen+4:] != PADDING[:numToPad]):
        return "INVALID PADDING"
    return(message)

message="test1"
encryptedMessage = encrypt(message)
unencryptedMessage = decrypt(encryptedMessage)
assert(unencryptedMessage == message)
