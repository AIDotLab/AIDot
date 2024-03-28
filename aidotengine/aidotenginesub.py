import os
import time
from datetime import datetime
from dotenv import load_dotenv
import boto3
import pymysql
import pika
import logging
from pathlib import Path

load_dotenv()
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = int(os.getenv("MYSQL_PORT"))
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWD = os.getenv("MYSQL_PASSWD")
MYSQL_DB = os.getenv("MYSQL_DB")
MYSQL_CHARSET = os.getenv("MYSQL_CHARSET")

RMQ_USERNAME = os.getenv("RMQ_USERNAME")
RMQ_PASSWORD = os.getenv("RMQ_PASSWORD")
RMQ_HOST_NAME = os.getenv("RMQ_HOST_NAME")
RMQ_PORT = os.getenv("RMQ_PORT")
RMQ_VIRTUAL_HOST = os.getenv("RMQ_VIRTUAL_HOST")

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_BUCKET_REGION = os.getenv("AWS_S3_BUCKET_REGION")
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")

CONS_REQUEST_CODE = os.getenv("CONS_REQUEST_CODE")
CONS_COMPLETE_CODE = os.getenv("CONS_COMPLETE_CODE")
CONS_PAUSE_CODE = os.getenv("CONS_PAUSE_CODE")
CONS_WORK_CODE = os.getenv("CONS_WORK_CODE")

logging.basicConfig (
  format = '%(asctime)s:%(levelname)s:%(message)s',
  datefmt = '%m/%d/%Y %I:%M:%S %p',
  level = logging.WARNING # DEBUG, INFO, WARNING, ERROR, CRITICAL
)

def connect_to_database():
    try:
        conn = pymysql.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, passwd=MYSQL_PASSWD, db=MYSQL_DB, charset=MYSQL_CHARSET)
        return conn
    except pymysql.Error as e:
        print(f"Error connecting to the database: {e}")
        return None

def RMQSend(topic, message):
    credentials = pika.PlainCredentials(RMQ_USERNAME, RMQ_PASSWORD)
    parameters = pika.ConnectionParameters(RMQ_HOST_NAME, RMQ_PORT, RMQ_VIRTUAL_HOST, credentials)
    connection = pika.BlockingConnection(parameters)
    try:
        channel = connection.channel()
        channel.queue_declare(queue=topic)
        channel.basic_publish(exchange='', routing_key=topic, body=str(message))
    finally:
        channel.close()
        connection.close()

def s3_connection():
    try:
        s3 = boto3.client(
            service_name='s3',
            region_name=AWS_S3_BUCKET_REGION,
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        print("s3 bucket connected!")
        return s3
    except Exception as e:
        print(e)
        #exit(ERROR_S3_CONNECTION_FAILED)
        return None

# TODO: 모델이 추가될때마다 수정해야 함
def tmp_get_AIModel(aimodel_code):
    models = {}
    models['YOLOv8Base'] = 'model/aidot/yolov8-base/yolov8s.pt'
    models['MMDetectionBase'] = 'model/aidot/mmdetection-base/dino-4scale_r50_improved_8xb2-12e_coco_20230818_162607-6f47a913.pth'
    models['화재 탐지'] = 'model/aidot/yolov8-base/yolov8s.pt'
    models['물고기 탐지'] = 'model/aidot/yolov8-base/yolov8s.pt'
    return models[aimodel_code]

def queue_process():
    credentials = pika.PlainCredentials(RMQ_USERNAME, RMQ_PASSWORD)
    parameters = pika.ConnectionParameters(RMQ_HOST_NAME, RMQ_PORT, RMQ_VIRTUAL_HOST, credentials)
    connection = pika.BlockingConnection(parameters)
    # Process 1. REQUEST AI 서버 큐 소비
    channel_request = connection.channel()
    channel_request.queue_declare(queue=THIS_REQUEST_CODE)
    # Process 2. COMPLETE AI 서버 큐 소비
    channel_complete = connection.channel()
    channel_complete.queue_declare(queue=THIS_COMPLETE_CODE)

    def callback_request(ch, method, properties, body):
        logging.warning("Message is Arrived {0} ({1})".format(THIS_REQUEST_CODE, eval(body)))
        # Process 1. REQUEST AI 서버 큐 소비 후, REQUEST AI 서버 큐 생성
        msq_body = eval(body)
        analysis_id = msq_body['analysis_id']
        aiserver_code = msq_body['aiserver_code']

        # 이미지 분석 정보 조회
        dbconn = connect_to_database()
        if not dbconn:
            logging.warning("DB Connection Error.")
            return 0
        dbcur = dbconn.cursor()

        try:
            sql = "SELECT * " \
                "  FROM aidot_ana_analysis_v " \
                " WHERE ana_public_flag = 'Y' " \
                "   AND ana_use_flag = 'Y' " \
                "   AND ana_analysis_id = %s "
            dbcur.execute(sql, analysis_id)
            ana_analysis = dbcur.fetchall()
        finally:
            dbcur.close()
            dbconn.close()

        if len(ana_analysis) == 0:
            logging.warning("No Analysis Request.")
            return 0
        
        # S3에서 이미지 갖고오기
        s3_object_name = ana_analysis[0][17]
        local_folder_path = os.path.join('data', str(ana_analysis[0][0]))
        Path(local_folder_path).mkdir(parents=True, exist_ok=True)
        local_file_path = os.path.join(local_folder_path, ana_analysis[0][16])

        s3 = s3_connection()
        try:
            s3.download_file(AWS_S3_BUCKET_NAME, s3_object_name, local_file_path)
        except Exception as e:
            logging.warning("S3 Download Error.")
            return 0

        # NOTICE: 실행되는 도커 이미지(컨테이너)가 자신의 AI Server Code('AIS101')를 알기 위해
        #         AIDOT ENGINE SUB Process에서 AIDOT ENGINE CORE Process로 AI Server Code를 전달되어야 함
        #         ex) MessageQueue: REQUEST-AIG101-AIS101
        #             analysis_id: 1000000005
        #             aiserver_code: AIG101-AIS101
        #             aimodel_path: /model/aidot/yolov8-base/yolov8s.pt
        #             data_path: data/1000000005/2024-03-22-03-10-14-dog2.jpg
        
        # TODO: AI 도커 컨테이너 실행

        # REQUEST-ID 큐 생성
        # TODO: tmp_get_AIModel 함수를 DB를 사용하는 방식으로 변경
        msq_body['aimodel_path'] = tmp_get_AIModel(ana_analysis[0][4])
        msq_body['data_folder_path'] = local_folder_path
        msq_body['data_file_name'] = ana_analysis[0][16]
        RMQSend(CONS_REQUEST_CODE + '-' + aiserver_code, msq_body)

    # Process 1. REQUEST AI 서버 큐 소비
    channel_request.basic_consume(queue=THIS_REQUEST_CODE,
                          on_message_callback=callback_request,
                          auto_ack=True)

    def callback_complete(ch, method, properties, body):
        logging.warning("Message is Arrived {0} ({1})".format(THIS_COMPLETE_CODE, eval(body)))
        # Process 2. COMPLETE AI 서버 큐 소비 소비 후, 사용이 끝난 AI 서버를 다시 휴지 상태로 변경
        msq_body = eval(body)
        analysis_id = msq_body['analysis_id']
        aiserver_code = msq_body['aiserver_code']
        aimodel_path = msq_body['aimodel_path'] # AI 모델 파일 경로
        data_folder_path = msq_body['data_folder_path']
        data_file_name = msq_body['data_file_name'] # 원본 Data 이름
        inf_file_name = msq_body['inf_file_name'] # 분석 Data 이름

        # S3에 분석 이미지 저장. 로컬 파일 삭제
        inf_file_path = os.path.join(data_folder_path, inf_file_name)
        save_s3_path = os.path.join('uploads', datetime.now().strftime('%Y%m%d%H'), inf_file_path)
        s3_image_url = f'https://{AWS_S3_BUCKET_NAME}.s3.{AWS_S3_BUCKET_REGION}.amazonaws.com/{save_s3_path}'

        if (os.path.isfile(inf_file_path)):
            s3 = s3_connection()
            try:
                s3.upload_file(inf_file_path, AWS_S3_BUCKET_NAME, save_s3_path)
            except Exception as e:
                logging.warning("S3 Upload Error.")
                return 0

        # AI 분석, AI 서버 정보 Table 수정
        dbconn = connect_to_database()
        if not dbconn:
            logging.warning("DB Connection Error.")
            return 0
        dbcur = dbconn.cursor()

        try:
            # AI 분석 정보 수정 
            sql = "update aidot_ana_analysis " \
                "   set ana_status_code = %s " \
                "     , ana_complete_date = SYSDATE() " \
                "     , ana_ana_s3_path = %s " \
                "     , ana_ana_s3_url = %s " \
                " where ana_analysis_id = %s"
            dbcur.execute(sql, (CONS_COMPLETE_CODE, save_s3_path, s3_image_url, analysis_id))

            # 사용이 끝난 AI 서버를 휴지 상태로 변경
            sql = "update aidot_com_aiserver " \
                "   set ais_status_code = %s " \
                " where ais_code = %s"
            dbcur.execute(sql, (CONS_PAUSE_CODE, aiserver_code))
            dbconn.commit()
        except Exception as e:
            print(e)
        finally:
            dbcur.close()
            dbconn.close()
        
        # 서버에 있는 파일 삭제
        try:
            if (os.path.isfile(os.path.join(data_folder_path, data_file_name))):
                os.remove(os.path.join(data_folder_path, data_file_name))
            if (os.path.isfile(os.path.join(data_folder_path, inf_file_name))):
                os.remove(os.path.join(data_folder_path, inf_file_name))
            if (os.path.isdir(data_folder_path)):
                os.rmdir(data_folder_path)
        except OSError as e:
            print("Error: %s : %s" % (f, e.strerror))   

    # Process 2. COMPLETE AI 서버 큐 소비
    channel_complete.basic_consume(queue=THIS_COMPLETE_CODE,
                          on_message_callback=callback_complete,
                          auto_ack=True)

    try:
        print("Waiting for messages.")
        channel_request.start_consuming()
        channel_complete.start_consuming()
    except KeyboardInterrupt:
        print('Ctrl+C is Pressed.')
    finally:
        channel_request.close()
        channel_complete.close()
        connection.close()

if __name__ == '__main__':
    # NOTICE: AI 서버 그룹('AIG101')은 .ENV에 정의되어 있어야 함
    THIS_AI_SERVER_GROUP = os.getenv("THIS_AI_SERVER_GROUP")
    THIS_REQUEST_CODE = CONS_REQUEST_CODE + '-' + THIS_AI_SERVER_GROUP
    THIS_COMPLETE_CODE = CONS_COMPLETE_CODE + '-' + THIS_AI_SERVER_GROUP
    
    queue_process()
