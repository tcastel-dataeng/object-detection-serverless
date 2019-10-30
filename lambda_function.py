import json
import urllib.parse
import boto3
import cv2
import numpy as np
import os
import sys
import tempfile
from utils import *


def load_file_content_from_S3(bucket_name, key):
        try:
            file_obj = s3.get_object(Bucket=bucket_name, Key=key)
            file_content = file_obj["Body"].read()
            return file_content   
        except Exception as e:
            print(e)
            print("""Error getting object {} in the bucket {}. Make sure they
            exist and your bucket is in the same region as this function."""
            .format(key, bucket_name))
        raise        

def read_image_from_S3(bucket_name, key):
        file_content = load_file_content_from_S3(bucket_name, key)
        np_array = np.fromstring(file_content, np.uint8)
        return cv2.imdecode(np_array, cv2.IMREAD_COLOR)

def download_temporary_file_from_S3_bis(bucket_name, key):

    localFilename = '/tmp/{}'.format(os.path.basename(key))
    try:    
        s3.download_file(Bucket=bucket_name, Key=key, Filename=localFilename) 
        return localFilename
    except Exception as e:
        print(e)
        print("""Error downloading  object {} in the bucket {}. Make sure they 
        exist and your bucket is in the same region as this function."""
        .format(key, bucket_name))
        raise e

def download_temporary_file_from_S3(bucket_name, key):

    localFilename = '/tmp/{}'.format(os.path.basename(key))
    f = tempfile.NamedTemporaryFile(delete=False)    
    f.write(load_file_content_from_S3(bucket_name, key)) 
    f.seek(0)
    
    return f.name    


def download_model_classes_from_S3(bucket_name, key):

    file_classes = load_file_content_from_S3(bucket_name, key)
    return file_classes.decode("utf-8").split("\n")


s3 = boto3.client('s3')

def lambda_handler(event, context):
    #print("Received event: " + json.dumps(event, indent=2))
    
    #Get the object from the event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse\
                .unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    
    #Read image and prepare classes
    image = read_image_from_S3(bucket_name, key)
    classes = download_model_classes_from_S3(bucket_name, "models/yolov3.txt")
    
    #Load model
    localFilename_cfg = download_temporary_file_from_S3(bucket_name, "models/yolov3-tiny.cfg")
    localFilename_weights = download_temporary_file_from_S3(bucket_name, "models/yolov3-tiny.weights")
    
    #Detect objects in an image write the detection on the image
    object_detection(image, classes, localFilename_weights, localFilename_cfg)

    #Create a new key for the image
    filename, file_extension = os.path.splitext(key)
    new_key = "transformedImages/"+filename[7:]+"ObjectDetection"+file_extension
    
    try:
        
        response = s3.put_object(Body=cv2.imencode('.jpg', image)[1].tostring(), Bucket=bucket_name, Key=new_key)
    
        return response
    except Exception as e:
        print(e)
        print("""Error put in object {} in the bucket {}. Make sure they 
        exist and your bucket is in the same region as this function."""
        .format(key, bucket_name))
        raise e
