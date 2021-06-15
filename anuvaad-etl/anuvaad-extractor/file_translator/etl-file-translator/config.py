import logging
import os

# Flask server
DEBUG = False
context_path = '/anuvaad-etl/file-translator'
HOST = '0.0.0.0'
PORT = 5001
ENABLE_CORS = False

# kafka
consumer_grp_default = 'anuvaad-etl-file-translator-consumer-group'
consumer_grp_identifier = 'KAFKA_ANUVAAD_ETL_FILE_TRANLATOR_CONSUMER_GRP'
CONSUMER_GROUP = os.environ.get(consumer_grp_identifier, consumer_grp_default)

# For Transform flow
input_topic_default = 'anuvaad-dp-tools-file-translator-transform-input-v1'
input_topic_identifier = 'KAFKA_ANUVAAD_DP_TOOLS_FT_INPUT'
transform_input_topic = os.environ.get(input_topic_identifier, input_topic_default)

output_topic_default = 'anuvaad-dp-tools-file-translator-transform-output-v1'
output_topic_identifier = 'KAFKA_ANUVAAD_DP_TOOLS_FT_OUTPUT'
transform_output_topic = os.environ.get(output_topic_identifier, output_topic_default)

# For download flow
input_topic_default = 'anuvaad-dp-tools-file-translator-download-input-v1'
input_topic_identifier = 'KAFKA_ANUVAAD_DP_TOOLS_FT_DOWNLOAD_INPUT'
download_input_topic = os.environ.get(input_topic_identifier, input_topic_default)

output_topic_default = 'anuvaad-dp-tools-file-translator-download-output-v1'
output_topic_identifier = 'KAFKA_ANUVAAD_DP_TOOLS_FT_DOWNLOAD_OUTPUT'
download_output_topic = os.environ.get(output_topic_identifier, output_topic_default)

kf_local_server = 'localhost:9092'
kafka_ip_host = 'KAFKA_BOOTSTRAP_SERVER_HOST'
bootstrap_server = os.environ.get(kafka_ip_host, kf_local_server)

# Fetch Content
FETCH_CONTENT_URL_VAR = 'FETCH_CONTENT_URL'
FETCH_CONTENT_URL_DEFAULT = 'https://auth.anuvaad.org/anuvaad/content-handler/v0/fetch-content'
FC_URL = os.environ.get(FETCH_CONTENT_URL_VAR, FETCH_CONTENT_URL_DEFAULT)

# folders and file path
download_folder = 'upload'

# DOCX CONFIG
DOCX_PARAGRAPH_GEN = True
DOCX_TABLE_DATA_GEN = True
DOCX_TABLE_OF_CONTENT_GEN = False
DOCX_HEADER_FOOTER_GEN = False

DOCX_PARAGRAPH_TRANS = True
DOCX_TABLE_DATA_TRANS = True
DOCX_TABLE_OF_CONTENT_TRANS = False
DOCX_HEADER_FOOTER_TRANS = False

DOCX_HYPERLINK_SUPPORT = False
DOCX_MULTI_PAGE = False
DOCX_MAX_PARA_IN_A_PAGE = 100

# PPTX CONFIG
PPTX_PARAGRAPH_GEN = True
PPTX_TABLE_DATA_GEN = True
PPTX_TABLE_OF_CONTENT_GEN = False
PPTX_HEADER_FOOTER_GEN = False

PPTX_PARAGRAPH_TRANS = True
PPTX_TABLE_DATA_TRANS = True
PPTX_TABLE_OF_CONTENT_TRANS = False
PPTX_HEADER_FOOTER_TRANS = False

PPTX_HYPERLINK_SUPPORT = False
PPTX_MULTI_PAGE = False
PPTX_MAX_PARA_IN_A_PAGE = 100

DOCX_FILE_PREFIX = 'DOCX-'


ALLOWED_FILE_TYPES = ['application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                      'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                      'application/json']
ALLOWED_FILE_EXTENSION = ['.docx', '.pptx', '.json']

logging.basicConfig(
    filename=os.getenv("SERVICE_LOG", "server.log"),
    level=logging.DEBUG,
    format="%(levelname)s: %(asctime)s \
        pid:%(process)s module:%(module)s %(message)s",
    datefmt="%d/%m/%y %H:%M:%S",
)
