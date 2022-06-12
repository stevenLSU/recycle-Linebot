from __future__ import unicode_literals
from flask import Flask, request, abort, render_template
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage
import requests
import json
import configparser
import os
import random
import string
from urllib import parse

from mysql.connector import pooling
from dotenv import load_dotenv

import numpy as np
import tensorflow as tf
from tensorflow import keras
from keras_preprocessing import image



app = Flask(__name__, static_url_path='/static')
UPLOAD_FOLDER = 'static'
ALLOWED_EXTENSIONS = set(['pdf', 'png', 'jpg', 'jpeg', 'gif'])


config = configparser.ConfigParser()
config.read('config.ini')

line_bot_api = LineBotApi(config.get('line-bot', 'channel_access_token'))
handler = WebhookHandler(config.get('line-bot', 'channel_secret'))
my_line_id = config.get('line-bot', 'my_line_id')
end_point = config.get('line-bot', 'end_point')
line_login_id = config.get('line-bot', 'line_login_id')
line_login_secret = config.get('line-bot', 'line_login_secret')
my_phone = config.get('line-bot', 'my_phone')
HEADER = {
    'Content-type': 'application/json',
    'Authorization': F'Bearer {config.get("line-bot", "channel_access_token")}'
}


def class_convert(classess):
    pred=[]
    for i in classess:
        if i ==0:
            pred.append('紙類')
        elif i==1:
            pred.append('鐵鋁罐')
        elif i==2:
            pred.append('紙容器')
        elif i==3:
            pred.append('塑膠容器')
        elif i==4:
            pred.append('一般垃圾')
    return pred

model = tf.keras.models.load_model('./model_v3.h5/')


@app.route("/", methods=['POST', 'GET'])
def index():
    global path
    if request.method == 'GET':
        return 'ok'
    body = request.json
    events = body["events"]
    print(body)
    if "replyToken" in events[0]:
        payload = dict()
        replyToken = events[0]["replyToken"]
        payload["replyToken"] = replyToken
        if events[0]["type"] == "message":
            if events[0]["message"]["type"] == "text":
                text = events[0]["message"]["text"]

                if text == "今日確診人數":
                    payload["messages"] = [
                            {
                                "type": "text",
                                "text": getTodayCovid19Message()
                            }
                        ]
                elif text == "開始辨識":
                    payload["messages"] = [
                        {
                            "type": "text",
                            "text": "開啟相機或點選圖庫照片，以開始辨識",
                            "quickReply": {
                                "items": [
                                    {
                                        "type": "action",
                                        "imageUrl": F"{end_point}/static/camera.png",
                                        "action": {
                                           "type": "camera",
                                            "label": "開啟相機"
                                        }
                                    },
                                    {
                                        "type": "action",
                                        "imageUrl": F"{end_point}/static/gallery.png",
                                        "action": {
                                            "type": "cameraRoll",
                                            "label": "開啟圖庫",
                                        }
                                    }
                                ]
                            }
                        }

                    ]
                elif text == "回收資訊":
                    payload["messages"] = [
                            {
                                "type": "template",
                                "altText": "This is a buttons template",
                                "template": {
                                    "type": "buttons",
                                    "thumbnailImageUrl": F"{end_point}/static/12.jpg",
                                    "imageSize": "cover",
                                    "title":"回收資訊",
                                    "text": "選擇查詢項目",
                                    "actions":[
                                      {
                                        "type": "message",
                                        "label": "紙容器",
                                        "text": "紙容器"
                                      },
                                      {
                                        "type": "message",
                                        "label": "鐵鋁罐",
                                        "text" : "鐵鋁罐"
                                      },
                                      {
                                        "type": "message",
                                        "label": "塑膠容器",
                                        "text": "塑膠容器"
                                     },
                                     {
                                        "type":"message",
                                        "label":"紙類",
                                        "text": "紙類"
                                      }
                                    ]
                                }
                            }
                        ]
                elif text == "紙容器":
                  payload["messages"] = [
                    {
                      "type": "image",
                      "label": "紙容器",
                      "originalContentUrl": F"{end_point}/static/paper.jpeg",
                      "previewImageUrl": F"{end_point}/static/paper.jpeg"
                                      }
                  ]
                elif text == "鐵鋁罐":
                  payload["messages"] = [
                    {
                      "type": "image",
                      "label": "鐵鋁罐",
                      "originalContentUrl": F"{end_point}/static/can.jpeg",
                      "previewImageUrl": F"{end_point}/static/can.jpeg"
                                      }
                  ]
                elif text == "塑膠容器":
                  payload["messages"] = [
                    {
                      "type": "image",
                      "label": "塑膠容器",
                      "originalContentUrl": F"{end_point}/static/plastic.jpeg",
                      "previewImageUrl": F"{end_point}/static/plastic.jpeg"
                                      }
                  ]
                elif text == "紙類":
                  payload["messages"] = [
                    {
                      "type": "image",
                      "label": "紙類",
                      "originalContentUrl": F"{end_point}/static/cardboard.jpeg",
                      "previewImageUrl": F"{end_point}/static/cardboard.jpeg"
                                      }
                  ]
                elif text == "Tensorflow模型":
                  def classify_image(my_image):
                      global result
                      custom_image = image.load_img(my_image, target_size=(224, 224))
                      img_array = image.img_to_array(custom_image)
                      processed_img = keras.applications.efficientnet_v2.preprocess_input(img_array).astype(np.float32)
                      swapped = np.moveaxis(processed_img, 0, 1)
                      arr4d = np.expand_dims(swapped, 0)
                      new_prediction = class_convert(np.argmax(model.predict(arr4d), axis=-1))
                      print('Your item is: ', new_prediction[0])
                      result = str(new_prediction[0])
                  classify_image(path)
                  payload["messages"] = [
                          {
                              "type": "text",
                              "text": F"判斷為:{result}"
                          }
                      ]
                elif text == "YOLOV5模型":

  
                  payload["messages"] = [
                          {
                              "type": "text",
                              "text": "開發中"
                          }
                      ]
                  
                  
                  
                  
                  
                  
                elif text == "聯絡我們":
                    payload["messages"] = [
                        {
                            "type": "template",
                            "altText": "this is a carousel template",
                            "template": {
                                "type": "carousel",
                                "columns": [
                                    {
                                        "thumbnailImageUrl": F"{end_point}/static/steven.jpg",
                                        "title": "林宣佑",
                                        "text": "世界上只有想不通的人，沒有走不通的路",
                                        "actions": [
                                            {
                                                "type": "uri",
                                                "label": "履歷",
                                                "uri": "https://drive.google.com/drive/u/0/folders/1f0YD5L0WfGyDPpavUtwWSxf0BMPyABZX"
                                            },
                                            {
                                                "type": "uri",
                                                "label": "git hub",
                                                "uri": "https://github.com/stevenLSU"
                                            }
                                        ]
                                    },
                                    {
                                        "thumbnailImageUrl": F"{end_point}/static/cts.jpg",
                                        "title": "邱子軒",
                                        "text": "全力以赴，盡其在我",
                                        "actions": [
                                            {
                                                "type": "uri",
                                                "label": "履歷",
                                                "uri": "https://drive.google.com/drive/u/1/folders/1H0ZBjS1f9H6B1ySzHbq7atpP-FxITO6J"
                                            },
                                            {
                                                "type": "uri",
                                                "label": "git hub",
                                                "uri": "https://github.com/Ben950128"
                                            }
                                        ]
                                    },
                                    {
                                        "thumbnailImageUrl": F"{end_point}/static/oscar1.jpg",
                                        "title": "黃巫剛",
                                        "text": "不經一事，不長一智",
                                        "actions": [
                                            {
                                                "type": "uri",
                                                "label": "履歷",
                                                "uri": "https://drive.google.com/file/d/1KJMDDK-doW53Ay-a35iEN8XpBhM5ARSY/view?usp=sharing"
                                            },
                                            {
                                                "type": "uri",
                                                "label": "git hub",
                                                "uri": "https://github.com/xlcso852456"
                                            }
                                        ]
                                    },
                                    {
                                        "thumbnailImageUrl": F"{end_point}/static/willy.jpg",
                                        "title": "方威竣",
                                        "text": "永遠沒有最好的時機，要就放手去做",
                                        "actions": [
                                            {
                                                "type": "uri",
                                                "label": "履歷",
                                                "uri": "https://drive.google.com/drive/folders/1BgK7g-RHuuN7Hr00vqJqFrtyyGIUuDSk"
                                            },
                                            {
                                                "type": "uri",
                                                "label": "git hub",
                                                "uri": "https://github.com/w1207qoo"
                                            }
                                        ]
                                    },
                                    {
                                        "thumbnailImageUrl": F"{end_point}/static/ching.jpeg",
                                        "title": "蔡佳蓉",
                                        "text": "真正激勵自己、打動人心的關鍵，不是你想了什麼，而是你付出行動去做！",
                                        "actions": [
                                            {
                                                "type": "uri",
                                                "label": "履歷",
                                                "uri": "https://drive.google.com/drive/folders/1553R5tvch5AHDswlu29-Pxpuy4ZznQiO"
                                            },
                                            {
                                                "type": "uri",
                                                "label": "git hub",
                                                "uri": "https://github.com/"
                                            }
                                        ]
                                    }
                                ]
                            }
                        }
                    ]
                else:
                    payload["messages"] = [
                            {
                                "type": "text",
                                "text": "請輸入正確指令"
                            }
                        ]
                replyMessage(payload)
            elif events[0]["message"]["type"] == "image":
                image_name = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(4))
                image_content = line_bot_api.get_message_content(events[0]["message"]["id"])
                image_name = image_name.upper() + '.jpg'
                path = './static/' + image_name
                with open(path, 'wb') as fd:
                    for chunk in image_content.iter_content():
                        fd.write(chunk)
                payload["messages"] = [
                            {
                                "type": "template",
                                "altText": "This is a buttons template",
                                "template": {
                                    "type": "buttons",
                                    "thumbnailImageUrl": F"{end_point}/static/12.jpg",
                                    "imageSize": "cover",
                                    "title":"模型",
                                    "text": "請選擇要使用的模型",
                                    "actions":[
                                      {
                                        "type": "message",
                                        "label": "Tensorflow模型",
                                        "text": "Tensorflow模型"
                                      },
                                      {
                                        "type": "message",
                                        "label": "YOLOV5模型",
                                        "text" : "YOLOV5模型"
                                      }
                                    ]
                                }
                            }
                        ]


                replyMessage(payload)



    return 'OK'




def getTodayCovid19Message():

    connection_pool = pooling.MySQLConnectionPool(
        pool_name="mysql_pool",
        pool_size=5,
        pool_reset_session=True,
        host=config.get("line-bot", "MYSQL_DB_HOST"),
        database=config.get("line-bot", "MYSQL_DB_DATABASE"),
        user=config.get("line-bot", "MYSQL_DB_USER"),
        password=config.get("line-bot", "MYSQL_DB_PASSWORD"),
        )
    connection_object = connection_pool.get_connection()
    cursor = connection_object.cursor()

    cursor.execute("select date, count, total_count from COVID19 order by COVID19_ID desc limit 1")
    records_covid = cursor.fetchall()
    date = records_covid[0][0]
    count = records_covid[0][1]
    total_count = records_covid[0][2]
    print(date, count, total_count)

    cursor.close()
    connection_object.close()
    return F"日期：{date}, 人數：{count}, 確診總人數：{total_count}"

def replyMessage(payload):
    response = requests.post("https://api.line.me/v2/bot/message/reply", headers=HEADER, data=json.dumps(payload))
    return 'OK'

if __name__ == "__main__":
    app.debug = True
    app.run()
