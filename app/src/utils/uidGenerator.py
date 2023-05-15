import uuid

def generateUuidToken():
    code = uuid.uuid4().hex
    uuid_token = str(code)
    return uuid_token