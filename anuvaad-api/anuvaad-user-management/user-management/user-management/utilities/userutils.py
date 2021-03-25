import uuid
import time
import re
import bcrypt
from db import get_db
from anuvaad_auditor.loghandler import log_info, log_exception
from anuvaad_auditor.errorhandler import post_error
import jwt
from utilities import MODULE_CONTEXT
import config
import json
import codecs
import requests
from flask_mail import Mail, Message
from app import mail
from flask import render_template

from config import USR_MONGO_COLLECTION,USR_TEMP_TOKEN_MONGO_COLLECTION,USR_TOKEN_MONGO_COLLECTION


role_codes_filepath = config.ROLE_CODES_URL
json_file_dir = config.ROLE_CODES_DIR_PATH
json_file_name = config.ROLE_CODES_FILE_NAME

mail_ui_link=config.BASE_URL
role_codes = []


class UserUtils:

    def __init__(self):
        pass
#useId generation
    @staticmethod
    def generate_user_id():
        return(uuid.uuid4().hex +str(time.time()).replace('.', '')[:13])
#email validation
    @staticmethod
    def validate_email(email):
        regex = '([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)'
        if (re.search(regex, email)):
            return True
        else:
            return False

#phone no validation
    # @staticmethod
    # def validate_phone(phone):
    #     Pattern = re.compile("(0/91)?[6-9][0-9]{9}")
    #     if (Pattern.match(phone)) and len(phone) == 10:
    #         return True
    #     else:
    #         return False

#password hashing
    @staticmethod
    def hash_password(password):
        password_in_byte = bytes(password, 'utf-8')  # converting str to byte
        salt = bcrypt.gensalt()
        return(bcrypt.hashpw(password_in_byte, salt))
#password validation (must 6 char range with upper,lower,special and number characters )
    @staticmethod
    def validate_password(password):
        if len(password) < config.MIN_LENGTH:
            return post_error("Invalid password", "password should be minimum 6 characteristics long", None)
        regex = ("^(?=.*[a-z])(?=." + "*[A-Z])(?=.*\\d)" +
                 "(?=.*[-+_!@#$%^&*., ?]).+$")
        pattern = re.compile(regex)
        if re.search(pattern, password) is None:
            return post_error("Invalid password", "password must contain atleast one uppercase,one lowercase, one numeric and one special character", None)


#validating rolecodes (rolecodes should match with the rolecodes read from json)
    @staticmethod
    def validate_rolecodes(roles):
        global role_codes
        if not role_codes:
            log_info("reading from remote location", MODULE_CONTEXT)
            role_codes = UserUtils.read_role_codes()
            # if role_codes is None:
            #     post_error("Data Null","Rolecodes read from json is none",None)
        log_info("ROLE_CODES:{}".format(role_codes), MODULE_CONTEXT)
        log_info("roles : {}".format(roles), MODULE_CONTEXT)
        
        for role in roles:
            try:
                if role not in role_codes:
                    return False
            except Exception:
                return post_error("Roles missing","No roles are read from json,empty json or invalid path",None)
#validating auth token of the user
    @staticmethod
    def token_validation(token):
        token_received = token
        if not token_received:
            return post_error("Invalid token", "Token recieved is empty", None)
        else:
            try:
                collections = get_db()[USR_TOKEN_MONGO_COLLECTION]      
                result = collections.find({"token": token_received}, {
                                          "_id": 0, "user": 1, "active": 1, "secret_key": 1})
                log_info("searching for record with the received token:{}".format(
                    result), MODULE_CONTEXT)
                if result.count() == 0:
                    return post_error("Invalid token", "Token received is not matching", None)
                for value in result:
                    if value["active"] == False:
                        return post_error("Invalid token", "Token has expired", None)
                    if value["active"] == True:
                        secret_key = value["secret_key"]

                        try:
                            jwt.decode(token, secret_key, algorithm='HS256')
                        except jwt.exceptions.ExpiredSignatureError as e:
                            log_exception("token expired",  MODULE_CONTEXT, e)
                            collections.update({"token": token}, {
                                "$set": {"active": False}})
                            return post_error("Invalid token", "Token has expired", None)
                        except Exception as e:
                            log_exception("invalid token",  MODULE_CONTEXT, e)
                            return post_error("Invalid token", "Not a valid token", None)
            except Exception as e:

                log_exception("db connection exception ",  MODULE_CONTEXT, e)
                return post_error("Database connection exception", "An error occurred while connecting to the database", None)
#searching for the user based on auth token
    @staticmethod
    def get_user_from_token(token,temp):
        token_received = token

        try: 
            if temp:
                document = USR_TEMP_TOKEN_MONGO_COLLECTION  
            else:
                document = USR_TOKEN_MONGO_COLLECTION  

            collections = get_db()[document] 
            result = collections.find(
                {"token": token_received}, {"_id": 0, "user": 1})
            log_info("search result for username in usertokens db matching the recieved token:{}".format(result), MODULE_CONTEXT)
            for record in result:
                username = record["user"]
        
        except Exception as e:
            log_exception("db connection exception ",  MODULE_CONTEXT, e)
            return post_error("Database connection exception", "An error occurred while connecting to the database", None)
        try:
            collections_usr = get_db()[USR_MONGO_COLLECTION]    #connector.get_mongo_instance(USR_MONGO_COLLECTION)    
            result_usr = collections_usr.find(
                {"userName": username,"is_verified":True}, {"_id": 0, "password": 0})
            log_info("record in users db matching the recieved token:{}".format(
                result), MODULE_CONTEXT)
            for record in result_usr:
                if record["is_active"]== False:
                    return post_error("Not active", "This operation is not allowed for an inactive user", None)
                return record
        except Exception as e:

            log_exception("db connection exception ",  MODULE_CONTEXT, e)
            return post_error("Database connection exception", "An error occurred while connecting to the database", None)
#retrieving token for the logged in user in case the token has already issued and valid
    @staticmethod
    def get_token(userName):
        try:
            collections = get_db()[USR_TOKEN_MONGO_COLLECTION]  #connector.get_mongo_instance()
            record = collections.find(
                {"user": userName, "active": True}, {"_id": 0, "token": 1, "secret_key": 1})
            log_info("search result for an active token matching the username:{}".format(
                record), MODULE_CONTEXT)

            if record.count() == 0:
                return {"status": "No token vailable for the user", "data": None}
            else:
                for value in record:
                    secret_key = value["secret_key"]
                    token = value["token"]
                    try:
                        jwt.decode(
                            token, secret_key, algorithm='HS256')
                        return({"status": True, "data": token})
                    except jwt.exceptions.ExpiredSignatureError as e:
                        log_exception(
                            "token matching the username has expired "+str(e),  MODULE_CONTEXT, e)
                        collections.update({"token": token}, {
                            "$set": {"active": False}})
                        return({"status": "Token has expired", "data": None})
                    except Exception as e:
                        log_exception(
                            "invalid token for the given username",  MODULE_CONTEXT, e)
                        return({"status": "Invalid token ", "data": None})
        except Exception as e:
            log_exception("db connection exception ",  MODULE_CONTEXT, e)
            return({"status": "Database connection exception", "data": None})

    @staticmethod
    def validate_user_input_creation(user):

        if "name" not in user or not user["name"]:
            return post_error("Data Missing", "name not found", None)
        if "userName" not in user or not user["userName"]:
            return post_error("Data Missing", "userName not found", None)
        if "password" not in user or not user["password"]:
            return post_error("Data Missing", "password not found", None)
        if "email" not in user or not user["email"]:
            return post_error("Data Missing", "email not found", None)
        if "roles" not in user or not user["roles"]:
            return post_error("Data Missing", "roles not found", None)
  
        password_validity = UserUtils.validate_password(user["password"])
        log_info("password validated:{}".format(password_validity), MODULE_CONTEXT)
        if password_validity is not None:
            return password_validity

        # if "phoneNo" in user and user["phoneNo"]:
            # if (UserUtils.validate_phone(user["phoneNo"])) == False:
            #     return post_error("Data not valid", "Phone number given is not valid", None)
        if UserUtils.validate_email(user["email"]) == False:
            return post_error("Data not valid", "Email Id given is not valid", None)
        try:
            collections = get_db()[USR_MONGO_COLLECTION]
            user_record = collections.find({'userName': user["userName"],"is_verified":True})
            if user_record.count() != 0:
                return post_error("Data not valid", "The username already exists. Please use a different username", None)
        except Exception as e:
            log_exception("db connection exception ",  MODULE_CONTEXT, e)
            return post_error("Database exception", "An error occurred while working on the database:{}".format(str(e)), None)

        rolecodes = []
        for rol in user["roles"]:
            if "roleCode" not in rol or not rol["roleCode"]:
                return post_error("Data Missing", "roleCode not found", None)
            rolecodes.append(rol["roleCode"])
        if UserUtils.validate_rolecodes(rolecodes) == False:
            return post_error("Invalid data", "Rolecode given is not valid", None)

    @staticmethod
    def validate_user_input_updation(user):
        if "userID" not in user or not user["userID"]:
            return post_error("Data Missing", "userID not found", None)
        if "name" not in user or not user["name"]:
            return post_error("Data Missing", "name not found", None)
        if "email" not in user.keys():
            return post_error("Data Missing", "email not found", None)
        

        userId = user["userID"]

        # if "phoneNo" in user and user["phoneNo"]:
            # if (UserUtils.validate_phone(user["phoneNo"])) == False:
            #     return post_error("Data not valid", "Phone number given is not valid", None)
        if UserUtils.validate_email(user["email"]) == False:
            return post_error("Data not valid", "Email Id given is not valid", None)
        try:
            collections = get_db()[USR_MONGO_COLLECTION]
            record = collections.find({'userID': userId,"is_verified":True})
            if record.count() == 0:
                return post_error("Data not valid", "No such verified user with the given Id", None)
            for value in record:
                if value["is_active"]== False:
                    return post_error("Not active", "This operation is not allowed for an inactive user", None)
        except Exception as e:
            log_exception("db connection exception ",  MODULE_CONTEXT, e)
            return post_error("Database connection exception", "An error occurred while connecting to the database:{}".format(str(e)), None)
        

    @staticmethod
    def validate_user_login_input(userName, Password):
        username = userName
        password = Password

        try:
            collections = get_db()[USR_MONGO_COLLECTION]
            result = collections.find({'userName': username,"is_verified":True}, {
                'password': 1, '_id': 0,'is_active':1})
            if result.count() == 0:
                return post_error("Not verified", "User account is not verified", None)
            for value in result:
                if value["is_active"]== False:
                    return post_error("Not active", "This operation is not allowed for an inactive user", None)
                password_in_db = value["password"].encode("utf-8")
                try:
                    if bcrypt.checkpw(password.encode("utf-8"), password_in_db)== False:
                        return post_error("Invalid Credentials", "Incorrect username or password", None)

                except Exception as e:
                    log_exception("exception while decoding password",  MODULE_CONTEXT, e)
                    return post_error("exception while decoding password", "exception:{}".format(str(e)), None)
                    
        except Exception as e:
            log_exception(
                "exception while validating username and password"+str(e),  MODULE_CONTEXT, e)
            return post_error("Database exception","Exception occurred:{}".format(str(e)),None)

#reading rolecodes from external json
    @staticmethod
    def read_role_codes():
        try:
            file = requests.get(role_codes_filepath, allow_redirects=True)
            file_path = json_file_dir + json_file_name
            open(file_path, 'wb').write(file.content)
            log_info("data read from git and pushed to local", MODULE_CONTEXT)
            with open(file_path, 'r') as stream:
                parsed = json.load(stream)
                roles = parsed['roles']
                log_info("roles read from json are {}".format(
                    roles), MODULE_CONTEXT)
                rolecodes = []
                for role in roles:
                    if role["active"]:
                        rolecodes.append(role["code"])
            log_info("rolecodes read from json is stored on to rolecodes array:{} ".format(
                rolecodes), MODULE_CONTEXT)
            return rolecodes
        except Exception as exc:
            log_exception("Exception while reading configs: " +
                          str(exc), MODULE_CONTEXT, exc)
            post_error("CONFIG_READ_ERROR",
                       "Exception while reading configs: " + str(exc), MODULE_CONTEXT)
#generating email notification for registered users
    @staticmethod
    def generate_email_user_creation(users):
        try:
            for user in users:
                email = user["userName"]   
                userId = user["userID"]
                msg = Message(subject="Welcome to Anuvaad",
                              sender="anuvaad.support@tarento.com",
                              recipients=[email])
                msg.html = render_template('register_mail_template.html',ui_link=mail_ui_link,activation_link=mail_ui_link+"activate/{}/{}/{}".format(email,userId,eval(str(time.time()).replace('.', '')[0:13])))
                mail.send(msg)
                log_info("generated email notification for user registration ", MODULE_CONTEXT)
        except Exception as e:
            log_exception("Exception while generating email notification for user registration: " +
                          str(e), MODULE_CONTEXT, e)
            return post_error("Exception while generating email notification for user registration","Exception occurred:{}".format(str(e)),None)
#generating email notification for forgot password
    @staticmethod
    def generate_email_reset_password(userName,rand_id):
        try:
            email = userName
            rand_id=rand_id


            msg = Message(subject="[Anuvaad] Please reset your Password ",
                              sender="anuvaad.support@tarento.com",
                              recipients=[email])
            msg.html = render_template('reset_mail_template.html',ui_link=mail_ui_link,reset_link=mail_ui_link+"set-password/{}/{}/{}".format(email,rand_id,eval(str(time.time()).replace('.', '')[0:13])))
            mail.send(msg)
            log_info("generated email notification for reset password", MODULE_CONTEXT)
        except Exception as e:
            log_exception("Exception while generating reset password notification: " +
                          str(e), MODULE_CONTEXT, e)
            return post_error("Exception while generating reset password notification","Exception occurred:{}".format(str(e)),None)
            
    @staticmethod
    def validate_username(usrName):
        try:
            collections = get_db()[USR_MONGO_COLLECTION]
            valid = collections.find({'userName':usrName,"is_verified":True})
            for value in valid:
                if value["is_active"]== False:
                    return post_error("Not active", "This operation is not allowed for an inactive user", None)
            log_info("search result on db for username/email validation, count of availability:{}".format(valid.count()), MODULE_CONTEXT)
            if valid.count() == 0:
                log_info("Not a valid email/username",MODULE_CONTEXT)
                return post_error("Not Valid","Given email/username is not associated with any of the active Anuvaad accounts",None)
        except Exception as e:
            log_exception("exception while validating username/email"+str(e),  MODULE_CONTEXT, e)
            return post_error("Database exception","Exception occurred:{}".format(str(e)),None)

      
    # @staticmethod
    # def get_nmt_models(model_ids):
    #     try:
    #         token="xxx"
    #         headers = {"Content-Type": "application/json","auth-token":token}
    #         request_url='https://auth.anuvaad.org//nmt-inference/v2/fetch-models?models={}'.format(model_ids)
    #         # request_url=config.NMT_FETCH_MODELS_URL
    #         # params=model_ids
    #         log_info("Intiating request to fetch data from %s"%request_url, MODULE_CONTEXT)
    #         response = requests.get(request_url, headers = headers)
    #         response_data = response.content
    #         log_info("Received data from fetch-content end point of content handler", MODULE_CONTEXT)
    #         dict_str = response_data.decode("UTF-8")
    #         dict_json_data = json.loads(dict_str)
    #         print(dict_json_data)
    #         # return dict_json_data
    #     except Exception as e:
    #         log_exception("exception while fectching models from NMT"+str(e),  MODULE_CONTEXT, e)
                

        