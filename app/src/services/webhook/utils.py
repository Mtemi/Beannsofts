from cryptography.fernet import Fernet


def generateKey():
    """create a key, CALLED ONCE OR WHEN NEED FOR CHANGING KEY ARISES"""
    key = Fernet.generate_key()
    with open("webhooks.secret.key", "wb") as key_file:
        key_file.write(key)


def loadKey():
    "Load previously generated key"
    return open("webhooks.secret.key", "rb").read()


def encryptMessage(message):
    """Encrypts a message"""
    key = loadKey()
    encodedMessage = message.encode()
    f = Fernet(key)
    encryptedMessage = f.encrypt(encodedMessage)

    return encryptedMessage


def decryptMessage(encryptedMessage):
    "decrypts the message"
    key = loadKey()
    f = Fernet(key)
    decryptMessage = f.decrypt(encryptedMessage)
    return decryptMessage.decode()
