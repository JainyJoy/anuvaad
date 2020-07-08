from flask import jsonify
import enum
from utilities.utils import FileOperation 
import config
from services.service import Pdf2HtmlService
import time
import logging

log = logging.getLogger('file')
file_ops = FileOperation()

class Status(enum.Enum):
    SUCCESS = {
        "status": "SUCCESS",
        "state": "PDF-TO-HTML-PROCESSED"
    }
    ERR_EMPTY_FILE_LIST = {
        "status": "FAILED",
        "state": "PDF-TO-HTML-PROCESSING",
        "error": {
            "code" : "NO_INPUT_FILES",
            "message" : "DO not receive any input files."
        }
    }
    ERR_FILE_NOT_FOUND = {
        "status": "FAILED",
        "state": "PDF-TO-HTML-PROCESSING",
        "error": {
            "code" : "FILENAME_ERROR",
            "message" : "No Filename given in input files."
        }
    }
    ERR_DIR_NOT_FOUND = {
        "status": "FAILED",
        "state": "PDF-TO-HTML-PROCESSING",
        "error": {
            "code" : "DIRECTORY_ERROR",
            "message" : "There is no input/output Directory."
        }
    }
    ERR_EXT_NOT_FOUND = {
        "status": "FAILED",
        "state": "PDF-TO-HTML-PROCESSING",
        "error": {
            "code" : "FILE_TYPE_ERROR",
            "message" : "This file type is not allowed. Currently, support only pdf file."
        }
    }
    ERR_locale_NOT_FOUND = {
        "status": "FAILED",
        "state": "PDF-TO-HTML-PROCESSING",
        "error": {
            "code" : "LOCALE_ERROR",
            "message" : "No language input or unsupported language input."
        }
    }
    ERR_jobid_NOT_FOUND = {
        "status": "FAILED",
        "state": "PDF-TO-HTML-PROCESSING",
        "error": {
            "code" : "JOBID_ERROR",
            "message" : "jobID is not given."
        }
    }
    ERR_Workflow_id_NOT_FOUND = {
        "status": "FAILED",
        "state": "PDF-TO-HTML-PROCESSING",
        "error": {
            "code" : "WORKFLOWCODE_ERROR",
            "message" : "workflowCode is not given."
        }
    }
    ERR_Tool_Name_NOT_FOUND = {
        "status": "FAILED",
        "state": "PDF-TO-HTML-PROCESSING",
        "error": {
            "code" : "TOOLNAME_ERROR",
            "message" : "toolname is not given"
        }
    }
    ERR_step_order_NOT_FOUND = {
        "status": "FAILED",
        "state": "PDF-TO-HTML-PROCESSING",
        "error": {
            "code" : "STEPORDER_ERROR",
            "message" : "step order is not given"
        }
    }
    ERR_pdf2html_conversion = {
        "status" : "FAILED",
        "state" : "PDF-TO-HTML-PROCESSING",
        "error": {
            "code" : "PDF2HTML_ERROR",
            "message" : "PDF2HTML failed. Something went wrong."
        }
    }
    ERR_Consumer = {
        "status" : "FAILED",
        "state" : "PDF-TO-HTML-PROCESSING",
        "error": {
            "code" : "KAFKA_CONSUMER_ERROR",
            "message" : "can not listen from consumer."
        }
    }
    ERR_Producer = {
        "status" : "FAILED",
        "state" : "PDF-TO-HTML-PROCESSING",
        "error": {
            "code" : "KAFKA_PRODUCER_ERROR",
            "message" : "No value received from consumer."
        }
    }
    ERR_request_input_format = {
        "status" : "FAILED",
        "state" : "PDF-TO-HTML-PROCESSING",
        "error": {
            "code" : "REQUEST_FORMAT_ERROR",
            "message" : "Json provided by user is not in proper format."
        }
    }


class CustomResponse():
    def __init__(self, status_code, jobid, workflow_id, tool_name, step_order, taskid, task_start_time, task_end_time, filename_response):
        self.status_code = status_code
        self.status_code['jobID'] = jobid
        self.status_code['taskID'] = taskid
        self.status_code['workflowCode'] = workflow_id
        self.status_code['taskStarttime'] = task_start_time
        self.status_code['taskendTime'] = task_end_time
        self.status_code['output'] = filename_response
        self.status_code['tool'] = tool_name
        self.status_code['stepOrder'] = step_order


class CheckingResponse(object):

    def __init__(self, json_data, task_id, task_starttime, DOWNLOAD_FOLDER):
        self.json_data = json_data
        self.task_id = task_id
        self.task_starttime = task_starttime
        self.DOWNLOAD_FOLDER = DOWNLOAD_FOLDER

    def wf_keyerror(self, jobid, workflow_id, tool_name, step_order, output_file_response):
        if jobid == "" or jobid is None:
            task_endtime = str(time.time()).replace('.', '')
            response = CustomResponse(Status.ERR_jobid_NOT_FOUND.value, jobid, workflow_id, tool_name, step_order,
                                            self.task_id, self.task_starttime, task_endtime, output_file_response)
            return response
        elif workflow_id == "" or workflow_id is None:
            task_endtime = str(time.time()).replace('.', '')
            response = CustomResponse(Status.ERR_Workflow_id_NOT_FOUND.value, jobid, workflow_id, tool_name, step_order,
                                            self.task_id, self.task_starttime, task_endtime, output_file_response)
            return response
        elif tool_name == "" or tool_name is None:
            task_endtime = str(time.time()).replace('.', '')
            response = CustomResponse(Status.ERR_Tool_Name_NOT_FOUND.value, jobid, workflow_id, tool_name, step_order,
                                            self.task_id, self.task_starttime, task_endtime, output_file_response)
            return response
        elif step_order == "" or step_order is None:
            task_endtime = str(time.time()).replace('.', '')
            response = CustomResponse(Status.ERR_step_order_NOT_FOUND.value, jobid, workflow_id, tool_name, step_order,
                                            self.task_id, self.task_starttime, task_endtime, output_file_response)
            return response
        response = False
        return response

    def service_response(self, jobid, workflow_id, tool_name, step_order,input_filepath, output_file_response):
        pdf_html_service = Pdf2HtmlService()
        try:
            output_htmlfiles_path, output_pngfiles_path = pdf_html_service.pdf2html(self.DOWNLOAD_FOLDER, input_filepath)
            outputfilepath = [output_htmlfiles_path, output_pngfiles_path]
            print(outputfilepath)
            return outputfilepath 
        except:
            task_endtime = str(time.time()).replace('.', '')
            response = CustomResponse(Status.ERR_pdf2html_conversion.value, jobid, workflow_id,  tool_name, step_order, 
                                            self.task_id, self.task_starttime, task_endtime, output_file_response)
            return response

    def input_file_response(self, jobid, workflow_id, tool_name, step_order, input_files, output_file_response, filename_response):
        output_htmlfiles_path, output_pngfiles_path = "", ""
        if len(input_files) == 0 or not isinstance(input_files, list):
            task_endtime = str(time.time()).replace('.', '')
            response = CustomResponse(Status.ERR_EMPTY_FILE_LIST.value, jobid, workflow_id, tool_name, step_order,
                                            self.task_id, self.task_starttime, task_endtime, output_file_response)
            return response
        else:
            for item in input_files:
                input_filename, in_file_type, in_locale = file_ops.accessing_files(item)
                input_filepath = file_ops.input_path(input_filename) #
                file_res = file_ops.one_filename_response(input_filename, output_htmlfiles_path, output_pngfiles_path, in_locale, in_file_type)
                filename_response.append(file_res)
                if input_filename == "" or input_filename is None:
                    task_endtime = str(time.time()).replace('.', '')
                    response = CustomResponse(Status.ERR_FILE_NOT_FOUND.value, jobid, workflow_id, tool_name, step_order,
                                                    self.task_id, self.task_starttime, task_endtime, output_file_response)
                    return response
                elif file_ops.check_file_extension(in_file_type) is False:
                    task_endtime = str(time.time()).replace('.', '')
                    response = CustomResponse(Status.ERR_EXT_NOT_FOUND.value, jobid, workflow_id, tool_name, step_order,
                                                    self.task_id, self.task_starttime, task_endtime, output_file_response)
                    return response
                elif file_ops.check_path_exists(input_filepath) is False or file_ops.check_path_exists(self.DOWNLOAD_FOLDER) is False:
                    task_endtime = str(time.time()).replace('.', '')
                    response = CustomResponse(Status.ERR_DIR_NOT_FOUND.value, jobid, workflow_id, tool_name, step_order,
                                                    self.task_id, self.task_starttime, task_endtime, output_file_response)
                    return response
                elif in_locale == "" or in_locale is None:
                    task_endtime = str(time.time()).replace('.', '')
                    response = CustomResponse(Status.ERR_locale_NOT_FOUND.value, jobid, workflow_id, tool_name, step_order,
                                                    self.task_id, self.task_starttime, task_endtime, output_file_response)
                    return response
                else:
                    output_filepath = self.service_response(jobid, workflow_id, tool_name, step_order,input_filepath, output_file_response)
                    print("filepaths", output_filepath)
                    if not isinstance(output_filepath, list):
                        if isinstance(output_filepath.status_code, dict):
                            return output_filepath
                    else:
                        file_res['outputHtmlFilePath'] = output_filepath[0]
                        file_res['outputImageFilePath'] = output_filepath[1]
        task_endtime = str(time.time()).replace('.', '')
        response_true = CustomResponse(Status.SUCCESS.value, jobid, workflow_id, tool_name, step_order, self.task_id, self.task_starttime,
                                                task_endtime, output_file_response)
        return response_true

    def only_input_file_response(self, input_files):
        output_htmlfiles_path, output_pngfiles_path = "", ""
        filename_response = list()
        if len(input_files) == 0 or not isinstance(input_files, list):
            response = Status.ERR_EMPTY_FILE_LIST.value
            return response
        else:
            for item in input_files:
                input_filename, in_file_type, in_locale = file_ops.accessing_files(item)
                input_filepath = file_ops.input_path(input_filename) #
                file_res = file_ops.one_filename_response(input_filename, output_htmlfiles_path, output_pngfiles_path, in_locale, in_file_type)
                filename_response.append(file_res)
                if input_filename == "" or input_filename is None:
                    response = Status.ERR_FILE_NOT_FOUND.value
                    return response
                elif file_ops.check_file_extension(in_file_type) is False:
                    response = Status.ERR_EXT_NOT_FOUND.value
                    return response
                elif file_ops.check_path_exists(input_filepath) is False or file_ops.check_path_exists(self.DOWNLOAD_FOLDER) is False:
                    response = Status.ERR_DIR_NOT_FOUND.value
                    return response
                elif in_locale == "" or in_locale is None:
                    response = Status.ERR_locale_NOT_FOUND.value
                    return response
                else:
                    pdf_html_service = Pdf2HtmlService()
                    try:
                        output_htmlfiles_path, output_pngfiles_path = pdf_html_service.pdf2html(self.DOWNLOAD_FOLDER, input_filepath) 
                        file_res['outputHtmlFilePath'] = output_htmlfiles_path
                        file_res['outputImageFilePath'] = output_pngfiles_path
                    except:
                        response = Status.ERR_pdf2html_conversion.value
            log.info("response generated from model response")
            response_true = {
                "status": "SUCCESS",
                "state": "SENTENCE-TOKENISED",
                "files" : filename_response
            }
            return response_true

    def main_response_wf(self):
        log.info("Response generation started")
        keys_checked = {'workflowCode','jobID','input','tool','stepOrder'}
        if self.json_data.keys() >= keys_checked:
            log.info("workflow request initiated.")
            input_files, workflow_id, jobid, tool_name, step_order = file_ops.input_format(self.json_data)
            filename_response = list()
            output_file_response = {"files" : filename_response}
            response_error = self.wf_keyerror(jobid, workflow_id, tool_name, step_order, output_file_response)
            if response_error is not False:
                log.error("workflow keys error")
                return response_error.status_code
            else:
                response_file = self.input_file_response(jobid, workflow_id, tool_name, step_order, input_files, output_file_response, filename_response)
                log.info("file response for wf generated")
                return response_file.status_code
        else:
            log.error("Input format is not correct")
            return Status.ERR_request_input_format.value

    def main_response_files_only(self):
        if self.json_data.keys() == {'files'}:
            log.info("request accepted")
            input_files = self.json_data['files']
            response = self.only_input_file_response(input_files)
            log.info("request processed")
            return response
        else:
            log.error("request format is not right.")
            return Status.ERR_request_input_format.value