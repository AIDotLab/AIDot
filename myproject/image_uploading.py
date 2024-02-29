from flask import Flask, render_template, url_for, redirect, request
from werkzeug.utils import secure_filename
import pika

#app = Flask(__name__)
app = Flask(__name__,
            static_folder='uploads')

RMQ_HOST_NAME = "localhost"
#RMQ_QUEUE_NAME = "snowdeer_queue"

def RMQSend(topic, message):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RMQ_HOST_NAME))
    try:
        channel = connection.channel()
        # props = BasicProperties(content_type='text/plain', delivery_mode=1)
        # channel.basic_publish('incoming', topic, message, props) # incoming exchange로 publish
        channel.queue_declare(queue=topic)
        channel.basic_publish(exchange='', routing_key=topic, body=message)
    finally:
        connection.close()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/upload')
def upload_file():
    return render_template('upload.html')

@app.route('/uploader', methods=['GET', 'POST'])
def uploader_file():
    if request.method == 'POST':
        f = request.files['file']
        #f.save(secure_filename(f.filename))
        f.save('uploads/ori.jpg')
        #return 'file uploaded successfully'

        RMQSend('REQUEST_A', 'request model A')
        RMQSend('REQUEST_B', 'request model B')
        
        return redirect(url_for('result'))

@app.route('/result')
def result():
    return render_template('result.html')

if __name__ == '__main__':
    #app.run(debug=True)
    app.run(host= '0.0.0.0')
