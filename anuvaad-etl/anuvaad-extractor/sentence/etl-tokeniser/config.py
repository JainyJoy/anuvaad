import logging
import os

# Flask server
DEBUG = False
context_path = '/anuvaad-etl/tokeniser-ocr'
HOST = '0.0.0.0'
PORT = 5001
ENABLE_CORS = False

# kafka
consumer_grp_default = 'anuvaad-etl-tokeniser-ocr-consumer-group'
consumer_grp_identifier = 'KAFKA_ANUVAAD_ETL_TOKENISER_OCR_CONSUMER_GRP'
CONSUMER_GROUP = os.environ.get(consumer_grp_identifier, consumer_grp_default)

input_topic_default = 'anuvaad-dp-tools-tokeniser-ocr-input-v1'
input_topic_identifier = 'KAFKA_ANUVAAD_DP_TOOLS_TOKENISER_OCR_INPUT'
input_topic = os.environ.get(input_topic_identifier, input_topic_default)

output_topic_default = 'anuvaad-dp-tools-tokeniser-ocr-output-v1'
output_topic_identifier = 'KAFKA_ANUVAAD_DP_TOOLS_TOKENISER_OCR_OUTPUT'
output_topic = os.environ.get(output_topic_identifier, output_topic_default)

kf_local_server = 'localhost:9092'
kafka_ip_host = 'KAFKA_BOOTSTRAP_SERVER_HOST'
bootstrap_server = os.environ.get(kafka_ip_host, kf_local_server)

#folders and file path
download_folder = 'upload'

logging.basicConfig(
    filename=os.getenv("SERVICE_LOG", "server.log"),
    level=logging.DEBUG,
    format="%(levelname)s: %(asctime)s \
        pid:%(process)s module:%(module)s %(message)s",
    datefmt="%d/%m/%y %H:%M:%S",
)
