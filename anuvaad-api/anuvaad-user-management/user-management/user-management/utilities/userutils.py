import uuid
import re
import bcrypt
from db import get_db
from passlib.hash import sha256_crypt

class UserUtils:

    def __init__(self):
        pass

    def generate_user_id():
        return(uuid.uuid4().hex)

    def validate_email(email):
        regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
        if (re.search(regex, email)):
            return email
        else:
            return("Invalid mail id")

    def validate_phone(phone):
        Pattern = re.compile("(0/91)?[6-9][0-9]{9}")
        if (Pattern.match(phone)) and len(phone) == 10:
            return phone
        else:
            return("Invalid phone number")

    def hash_password(password):
        salt = bcrypt.gensalt()
        return(bcrypt.hashpw(password, salt))


    def encrypt_password(password):
            encrypted_password = sha256_crypt.encrypt(password)
            return(encrypted_password)

#     def decrypt_password(encrypted_password):
#             """
#             Decrypts an encrypted message
#             """
#             key = load_key()
#             f = Fernet(key)
#             decrypted_password = f.decrypt(encrypted_password)
#             return(decrypted_password.decode())

    def validate_userid(usrId):
            collections = get_db()['sample']
            valid = collections.find({ 'userID': {'$in': [usrId]}})
            if valid.count() != 0:
                    userID = UserUtils.generate_user_id()
                    validate_userid(userID)
            else:
                    return(usrId)

    def validate_username(usrName):
            collections = get_db()['sample']
            valid = collections.find({ 'userName': {'$in': [usrName]}})
            if valid.count() != 0:
                    return(False)
            else:
                    return(usrName)

                    


