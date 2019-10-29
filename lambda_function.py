import json
import urllib.parse
import boto3
import cv2
import numpy as np
import os
import sys
from utils import *

def load_file_content_from_S3 (bucket_name,key):
        try:
            file_obj = s3.get_object(Bucket=bucket_name, Key=key)
            file_content = file_obj["Body"].read()
            return file_content    
        except Exception as e:
            print(e)
            print('Error getting object {} in the bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket_name))
        raise        

def read_image_from_S3(bucket_name,key):
        file_content = load_file_content_from_S3(bucket_name,key)
        np_array = np.fromstring(file_content, np.uint8)
        return cv2.imdecode(np_array, cv2.IMREAD_COLOR)

def download_temporary_file_from_S3(bucket_name,key):

    localFilename = '/tmp/{}'.format(os.path.basename(key))
    try:    
        s3.download_file(Bucket=bucket_name, Key=key, Filename=localFilename) 
        return localFilename
    except Exception as e:
        print(e)
        print('Error downloading  object {} in the bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket_name))
        raise e

def download_model_classes_from_s3(bucket_name,key):

    file_classes = load_file_content_from_S3(bucket_name,key)
    return file_classes.decode("utf-8").split("\n")


s3 = boto3.client('s3')

def lambda_handler(event, context):
    #print("Received event: " + json.dumps(event, indent=2))
    
    # Get the object from the event and show its content type
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    
    #Read image and prepare classes
    image = read_image_from_S3(bucket_name,key)
    classes = download_model_classes_from_s3(bucket_name,"models/yolov3.txt")
    
    #load model
    localFilename_cfg = download_temporary_file_from_S3(bucket_name,"models/yolov3-tiny.cfg")
    localFilename_weights = download_temporary_file_from_S3(bucket_name,"models/yolov3-tiny.weights")
    net = cv2.dnn.readNet(localFilename_weights, localFilename_cfg)
    
    #prepare model
    scale = 0.00392
    blob = cv2.dnn.blobFromImage(image, scale, (416,416), (0,0,0), True, crop=False)
    net.setInput(blob)
    
    #Apply model
    outs = net.forward(get_output_layers(net))

    #Keep relevant predictions
    boxes, confidences, class_ids = keep_relevant_predictions(outs=outs,width=image.shape[1],height=image.shape[0])
    
    #Apply NMS
    conf_threshold = 0.5
    nms_threshold = 0.4
    indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)
    
    #Draw Bounding Box
    colors = np.random.uniform(0, 255, size=(len(classes), 3))
    draw_bounding_boxes(image,boxes,indices,class_ids, classes,confidences,colors)
 
        
    try:
        filename, file_extension = os.path.splitext(key)
        
        new_key = "transformedImages/"+filename[7:]+"ObjectDetection"+file_extension
        response = s3.put_object(Body=cv2.imencode('.jpg', image)[1].tostring(), Bucket=bucket_name, Key=new_key)
    
        return response
    except Exception as e:
        print(e)
        print('Error put in object {} in the bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket_name))
        raise e
