import json
import urllib.parse
import boto3
import cv2
import numpy as np
import os
import sys
import time


def load_file_content_from_S3 (bucket_name,key):
        file_obj = s3.get_object(Bucket=bucket_name, Key=key)
        file_content = file_obj["Body"].read()
        return file_content

def list_S3_object(bucket_name):
    print(s3.list_objects_v2(Bucket=bucket_name))

def read_image_from_S3(bucket_name,key):
        file_content = load_file_content_from_S3(bucket_name,key)
        np_array = np.fromstring(file_content, np.uint8)
        return cv2.imdecode(np_array, cv2.IMREAD_COLOR)

def download_temporary_file_from_S3(bucket_name,key):

    localFilename = '/tmp/{}'.format(os.path.basename(key))
    try:    
        s3.download_file(Bucket=bucket_name, Key=key, Filename=localFilename_cfg) 
        return localFilename
    except Exception as e:
        print(e)
        print('Error downloading  object {} in the bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket_name))
        raise e
    

    
    #localFilename_cfg = '/tmp/{}'.format(os.path.basename("models/yolov3.cfg"))
    #localFilename_weights = '/tmp/{}'.format(os.path.basename("models/yolov3.weights"))
    
    #s3.download_file(Bucket=bucket_name, Key="models/yolov3-tiny.cfg", Filename=localFilename_cfg)
    #s3.download_file(Bucket=bucket_name, Key="models/yolov3-tiny.weights", Filename=localFilename_weights)



s3 = boto3.client('s3')

def lambda_handler(event, context):
    #print("Received event: " + json.dumps(event, indent=2))
    
    def get_output_layers(net):
    
        layer_names = net.getLayerNames()
        output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]

        return output_layers

    def download_model_classes_from_s3(bucket_name,key):

        file_classes = load_file_content_from_S3(bucket_name,key)
        return file_classes.decode("utf-8").split("\n")


    def draw_prediction(img, class_id, confidence, x, y, x_plus_w, y_plus_h):

        label = str(classes[class_id]) + str(format(confidence * 100, '.2f')) + '%'
        color = COLORS[class_id]

        cv2.rectangle(img, (x,y), (x_plus_w,y_plus_h), color, 2)
        cv2.putText(img, label, (x-10,y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)


    def draw_bounding_boxes(image,boxes,indices):
        for i in indices:
            i = i[0]
            box = boxes[i]
            x = box[0]
            y = box[1]
            w = box[2]
            h = box[3]
            draw_prediction(image, class_ids[i], confidences[i], round(x), round(y), round(x+w), round(y+h))
    
    start = time.time()
    
    # Get the object from the event and show its content type
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    
    ############################################################################
    image = read_image_from_S3(bucket_name,key)

    
    getimage = time.time()   
    print("time to get image :",getimage - start)
    
    classes = download_model_classes_from_s3(bucket_name,"models/yolov3.txt")
    COLORS = np.random.uniform(0, 255, size=(len(classes), 3))
    
    
    getclasses = time.time()   
    print("time to create classes :",getclasses-getimage)
    

    localFilename_cfg = download_temporary_file_from_S3(bucket_name,"models/yolov3-tiny.cfg")
    localFilename_weights = download_temporary_file_from_S3(bucket_name,"models/yolov3-tiny.weights")
    
    getdl = time.time()   
    print("time to download files :",getdl-getclasses)
    
    net = cv2.dnn.readNet(localFilename_weights, localFilename_cfg)
    
    

    
    ##########################################################################
    Width = image.shape[1]
    Height = image.shape[0]
    scale = 0.00392
    
    blob = cv2.dnn.blobFromImage(image, scale, (416,416), (0,0,0), True, crop=False)

    net.setInput(blob)
    
    createmodel = time.time()   
    print("time to create model :",createmodel-getdl)

    
    outs = net.forward(get_output_layers(net))
    
    applymodel = time.time()   
    print("time to applymodel :",applymodel-createmodel)
    
    class_ids = []
    confidences = []
    boxes = []
    conf_threshold = 0.5
    nms_threshold = 0.4
    
    
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                center_x = int(detection[0] * Width)
                center_y = int(detection[1] * Height)
                w = int(detection[2] * Width)
                h = int(detection[3] * Height)
                x = center_x - w / 2
                y = center_y - h / 2
                class_ids.append(class_id)
                confidences.append(float(confidence))
                boxes.append([x, y, w, h])
    
    
    indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)
    

    draw_bounding_boxes(image,boxes,indices)

    getbox = time.time()   
    print("time to draw boxes :",getbox-applymodel)    
        
    try:
        filename, file_extension = os.path.splitext(key)
        
        new_key = "transformedImages/"+filename[7:]+"ObjectDetection"+file_extension
        response = s3.put_object(Body=cv2.imencode('.jpg', image)[1].tostring(), Bucket=bucket_name, Key=new_key)
        putobject = time.time()   
        print("time to put object in s3 :",putobject-getbox) 
        return response
    except Exception as e:
        print(e)
        print('Error put in object {} in the bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket_name))
        raise e
