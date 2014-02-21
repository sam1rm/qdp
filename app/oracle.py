import base64

from Crypto.Cipher import AES
from Crypto import Random

globals={}

KEY_KEY = "key"
ENCRYPTED_PREFIX_FLAG_KEY = "enc_pre_flag"
PADDING_KEY = "padding"

MAX_SIZE_DIGITS = 8 

""" Encryption and decryption 'Oracle' singleton:
    http://stackoverflow.com/questions/6841853/python-accessing-module-scope-vars/6842257#6842257 
    Primarily created to store an 'encryptedPrefixFlag,'
    which allows us to (more) accurately determine if a message is encrypted or not. 
    A regex expression doesn't seem accurate enough: 
    (e.g. http://stackoverflow.com/questions/8571501/how-to-check-whether-the-string-is-base64-encoded-or-not) """

def init(key, encryptedPrefixFlag, padding= "0123456789abcdef"):
    if ((len(key) != 16) and (len(key) != 24) and (len(key) != 32)):
        raise Exception("AES key must be either 16, 24, or 32 bytes long")
    globals[KEY_KEY] = key
    globals[ENCRYPTED_PREFIX_FLAG_KEY] = encryptedPrefixFlag
    globals[PADDING_KEY] = padding

def generateIV():
    """ Generate a 16-byte, random IV, then return the raw data as well as the base64 encoded version (for saving in the DB) """
    iv = Random.new().read(AES.block_size)
    return iv, base64.b64encode(iv)

def encrypt( message, IV):
    """ Encrypt a 16-byte, length-prefixed, padded message using AES.
        Returned message is base64 encoded.
    >>> init('cecb3442f0203f52693295e1e3d07c63', encryptedPrefixFlag='DocTest'); iv,b64iv=generateIV(); message=encrypt("this is a test",iv); decrypt(message,b64iv)
    'this is a test'
    >>> init('cecb3442f0203f52693295e1e3d07c63', encryptedPrefixFlag='DocTest'); iv,b64iv=generateIV(); message=encrypt("this is a test",iv); decrypt(message,b64iv)
    'this is a test'
    >>> init('cecb3442f0203f52693295e1e3d07c63', encryptedPrefixFlag='DocTest'); iv,b64iv=generateIV(); message=encrypt("THIS 0 IS 1 A 2 TEST 3",iv); decrypt(message,b64iv)
    'THIS 0 IS 1 A 2 TEST 3'
    >>> init('cecb3442f0203f52693295e1e3d07c63', encryptedPrefixFlag='DocTest'); iv,b64iv=generateIV(); message=encrypt("  THIS 0 IS 1 A 2 TEST 3  ",iv); decrypt(message,b64iv)
    '  THIS 0 IS 1 A 2 TEST 3  '
    >>> init('cecb3442f0203f52693295e1e3d07c63', encryptedPrefixFlag='DocTest'); iv,b64iv=generateIV(); message=encrypt("QDPTHIS_IS_A_TESTQDP",iv); decrypt(message,b64iv)
    'QDPTHIS_IS_A_TESTQDP'
    """
    assert(message)
    assert(IV)
    assert(len(IV)==16),"Length of IV is incorrect"
    assert(len(message) < 10**MAX_SIZE_DIGITS), "Message is too long (%d > %d)" % (len(message), 10**MAX_SIZE_DIGITS)
    OBJ = AES.new(globals[KEY_KEY], AES.MODE_CBC, IV)
    numToPad = 16 - ( len(message) + MAX_SIZE_DIGITS ) % 16
    paddedMessage = "%08d%s%s" % (len(message),message,globals[PADDING_KEY][:numToPad]) # First format must == MAX_SIZE_DIGITS
    assert(len(paddedMessage)%16 == 0),"len(paddedMessage) is not a multiple of 16! ("+str(len(paddedMessage))+"%"+str(len(paddedMessage)%16)+")"
    encryptedMessage = OBJ.encrypt(paddedMessage)
    return(globals[ENCRYPTED_PREFIX_FLAG_KEY]+base64.b64encode(encryptedMessage))

def isEncrypted( message):
    """ Prefix message to allow detection for encrypted messages. More reliable than some crazy
        regex expression trying to determine if the message fits a pattern (e.g. base64 encoded)
    >>> init('cecb3442f0203f52693295e1e3d07c63', encryptedPrefixFlag='QDP'); print isEncrypted("QDPblahblahblah")
    True
    >>> init('cecb3442f0203f52693295e1e3d07c63', encryptedPrefixFlag='QDP'); print isEncrypted("blahblahblahQDP")
    False
    >>> init('cecb3442f0203f52693295e1e3d07c63', encryptedPrefixFlag='QDP'); print isEncrypted("qdpblahblahblahQDP")
    False
    """
    if message:
        if (message[:len(globals[ENCRYPTED_PREFIX_FLAG_KEY])] == globals[ENCRYPTED_PREFIX_FLAG_KEY]):
            return True
    return False

def decrypt( encodedMessage, IV):
    """ Decode a base64 message using AES. Returned is original message minus the padding,
        which is checked for integrity (the length is also a prefix integrity checker) 
        (see sister function encrypt for tests). """
    message = None
    if isEncrypted(encodedMessage):
        b64Message = encodedMessage[len(globals[ENCRYPTED_PREFIX_FLAG_KEY]):]
        try:
            iv = base64.b64decode(IV)
        except TypeError as ex:
            raise Exception("INVALID IV for decryption: "+str(ex))
        OBJ = AES.new(globals[KEY_KEY], AES.MODE_CBC, iv)
        try:
            message = base64.b64decode(b64Message)
        except TypeError as ex:
            raise Exception("INVALID b64Message to decrypt: "+str(ex))
        paddedMessage = OBJ.decrypt(message)
        try:
            messageLen = int(paddedMessage[:MAX_SIZE_DIGITS])
        except ValueError as ex:
            raise Exception("INVALID LENGTH in paddedMessage: "+str(ex))
        numToPad = 16 - ( messageLen + MAX_SIZE_DIGITS ) % 16
        message = paddedMessage[MAX_SIZE_DIGITS:messageLen+MAX_SIZE_DIGITS]
        if (paddedMessage[messageLen+MAX_SIZE_DIGITS:] != globals[PADDING_KEY][:numToPad]):
            raise Exception("INVALID PADDING in paddedMessage: "+str(ex))
    else:
        raise Exception("INVALID isEncrypted prefix (trying to decrypt something already decrypted?)")
    return(message)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
