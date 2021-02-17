from flask_restful import fields, marshal_with, reqparse, Resource
from repositories import UserAuthenticationRepositories
from models import CustomResponse, Status
from utilities import UserUtils
from utilities import MODULE_CONTEXT,AppContext
import ast
from anuvaad_auditor.loghandler import log_info, log_exception
from flask import request
from anuvaad_auditor.errorhandler import post_error
import datetime




class UserLogin(Resource):

    def post(self):
        body = request.get_json()
        if "userName" not in body or not body["userName"]:
            return post_error("Data Missing","userName not found",None), 400
        if "password" not in body or not body["password"]:
            return post_error("Data Missing","password not found",None), 400
        
        userName = body["userName"]
        password = body["password"]

        AppContext.adduserName(userName)
        log_info("Request for login",MODULE_CONTEXT)
        validity=UserUtils.validate_user_login_input(userName, password)
        
        if validity is not None:
                return validity, 400
        AppContext.adduserName(userName)
        log_info("Login credentials validated ",MODULE_CONTEXT)
        try:
            result = UserAuthenticationRepositories.user_login(
                userName, password)
            AppContext.adduserName(userName)
            log_info("User login result:{}".format(result),MODULE_CONTEXT)
            if result == False:
                res = CustomResponse(
                    Status.FAILURE_USR_LOGIN.value, None)
                return res.getresjson(), 400

            res = CustomResponse(Status.SUCCESS_USR_LOGIN.value, result)
            return res.getresjson(), 200
        except Exception as e:
            AppContext.adduserName(userName)
            log_exception("Exception while  user login: " +
                      str(e), MODULE_CONTEXT, e)
            return post_error("Exception occurred", "Exception while performing user login", None), 400
            


class UserLogout(Resource):

    def post(self):
        body = request.get_json()
        if "userName" not in body or not body["userName"]:
            return post_error("Data Missing","userName not found",None), 400
        userName = body["userName"]

        AppContext.adduserName(userName)
        log_info("Request for logout",MODULE_CONTEXT)
        try:
            result = UserAuthenticationRepositories.user_logout(userName)
            AppContext.adduserName(userName)
            log_info("User logout result:{}".format(result),MODULE_CONTEXT)
            if result == False:
                res = CustomResponse(
                    Status.FAILURE_USR_LOGOUT.value, None)
                return res.getresjson(), 400
            else:
                res = CustomResponse(Status.SUCCESS_USR_LOGOUT.value, None)
            return res.getres()
        except Exception as e:
            log_exception("Exception while logout: " +
                      str(e), MODULE_CONTEXT, e)
            return post_error("Exception occurred", "Exception while performing user logout", None), 400
            


class AuthTokenSearch(Resource):

    def post(self):
        body = request.get_json()
        
        if "token" not in body or not body["token"]:
            return post_error("Data Missing","token not found",None), 400
        token = body["token"]
        log_info("Request for token search",MODULE_CONTEXT)
        if len(token.split('.')) ==3:
            temp = False
            validity=UserUtils.token_validation(token)
            log_info("Token validation result:{}".format(validity),MODULE_CONTEXT)
            if validity is not None:
                    return validity, 400
        else:
            temp = True

        try:
            result = UserAuthenticationRepositories.token_search(token,temp)
            log_info("User auth token search result:{}".format(result),MODULE_CONTEXT)
            if result == False:
                res = CustomResponse(
                    Status.FAILURE_USR_TOKEN.value, None)
                return res.getresjson(), 400
            else:
                res = CustomResponse(Status.SUCCESS_USR_TOKEN.value, result)
            return res.getres()
        except Exception as e:
            log_exception("Exception while user auth search: " +
                      str(e), MODULE_CONTEXT, e)
            return post_error("Exception occurred", "Exception while performing user creation", None), 400
            

class ForgotPassword(Resource):
        
    def post(self):
        body = request.get_json()
        if "userName" not in body or not body["userName"]:
            return post_error("Data Missing","userName not found",None), 400
        userName = body["userName"]

        AppContext.adduserName(userName)
        log_info("Request for reset password link",MODULE_CONTEXT)
        validity = UserUtils.validate_username(userName)
        log_info("Username/email is validated for generating reset password notification:{}".format(validity), MODULE_CONTEXT)
        if validity is not None:
            return validity, 400
        try:
            result = UserAuthenticationRepositories.forgot_password(userName)
            log_info("Forgot password api call result:{}".format(result),MODULE_CONTEXT)
            if result == True:
                res = CustomResponse(
                        Status.SUCCESS_FORGOT_PWD.value, None)
                return res.getresjson(), 200
            else:
                return result, 400
        except Exception as e:
            log_exception("Exception while forgot password api call: " +
                        str(e), MODULE_CONTEXT, e)
            return post_error("Exception occurred", "Exception while forgot password api call:{}".format(str(e)), None), 400
            
        




class ResetPassword(Resource):

    def post(self):
        
        body = request.get_json()
        if "userName" not in body or not body["userName"]:
            return post_error("Data Missing","userName not found",None), 400
        if "password" not in body or not body["password"]:
            return post_error("Data Missing","Password not found",None), 400

        userId=request.headers["x-user-id"]
        userName = body["userName"]
        password = body["password"]
        
        AppContext.adduserName(userName)
        AppContext.addUserID(userId)
        log_info("Request for password resetting",MODULE_CONTEXT)
        if not userId:
            return post_error("userId missing","userId is mandatory",None), 400
        
        validity = UserUtils.validate_username(userName)
        log_info("Username/email is validated for resetting password:{}".format(validity), MODULE_CONTEXT)
        pwd_validity=UserUtils.validate_password(password)
        log_info("password is validated for resetting password:{}".format(pwd_validity), MODULE_CONTEXT)
        
        if validity is not None:
            return validity, 400
        
        if pwd_validity is not None:
            return pwd_validity, 400
            
        try:
            result = UserAuthenticationRepositories.reset_password(userId,userName,password)
            log_info("Reset password api call result:{}".format(result),MODULE_CONTEXT)
            if result == True:
                res = CustomResponse(
                        Status.SUCCESS_RESET_PWD.value, None)
                return res.getresjson(), 200
            else:
                res = CustomResponse(Status.FAILURE_RESET_PWD.value,None)
                return res.getresjson(), 400
        except Exception as e:
            log_exception("Exception while forgot password api call: " +
                        str(e), MODULE_CONTEXT, e)
            return post_error("Exception occurred", "Exception while reset password api call:{}".format(str(e)), None), 400


class VerifyUser(Resource):

    def post(self):
        body = request.get_json()
        if "userName" not in body or not body["userName"]:
            return post_error("Data Missing","userName not found",None), 400
        if "userID" not in body or not body["userID"]:
            return post_error("Data Missing","userID not found",None), 400
        user_email = body["userName"]
        user_id = body["userID"]

        AppContext.adduserName(user_email)
        AppContext.addUserID(user_id)
        log_info("Request for password resetting",MODULE_CONTEXT)
        try:
            result = UserAuthenticationRepositories.verify_user(user_email,user_id)
            log_info("Activate user api call result:{}".format(result),MODULE_CONTEXT)
            if result is not None:
                return result, 400
            else:
                res = CustomResponse(
                        Status.SUCCESS_ACTIVATE_USR.value, None)
                return res.getresjson(), 200
            
        except Exception as e:
            log_exception("Exception while Activate user api call: " +
                        str(e), MODULE_CONTEXT, e)
            return post_error("Exception occurred", "Exception while Activate user api call:{}".format(str(e)), None), 400

class ActivateDeactivateUser(Resource):

    def post(self):
        body = request.get_json()
        if "userName" not in body or not body["userName"]:
            return post_error("Data Missing","userName not found",None), 400
        if "is_active" not in body:
            return post_error("Data Missing","is_active not found",None), 400
        user_email = body["userName"]
        status= body["is_active"]

        if not isinstance(status,bool):
            return post_error("Invalid format", "status should be bool", None), 400

        AppContext.adduserName(user_email)
        log_info("Request for updating user activation status",MODULE_CONTEXT)
        try:
            result = UserAuthenticationRepositories.activate_deactivate_user(user_email,status)
            log_info("Deactivate user api call result:{}".format(result),MODULE_CONTEXT)
            if result is not None:
                return result, 400
            else:
                res = CustomResponse(
                        Status.SUCCESS.value, None)
                return res.getresjson(), 200
            
        except Exception as e:
            log_exception("Exception while deactivate user api call: " +
                        str(e), MODULE_CONTEXT, e)
            return post_error("Exception occurred", "Exception while deactivate user api call:{}".format(str(e)), None), 400
