from flask import Blueprint
from flask_restful import Api
from src.resources.module import OCR


# end-point for independent service
OCR_BLUEPRINT = Blueprint("ocr", __name__)
api = Api(OCR_BLUEPRINT)
api.add_resource(OCR, "/v0/ulca-ocr")
