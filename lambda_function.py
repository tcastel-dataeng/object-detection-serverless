#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author : Théo Castel
# Python 
# version 3.7.4

"""A simple lamnda that detect object on an image.

 This lambda is triggered by an S3 event by uploading a photo to the S3.
 It then detect object on the photo and write pertinent prediction on the
 photo with bounding boxes.

 """


import json
import urllib.parse
import boto3
import cv2
import numpy as np
import os
import sys
import tempfile
from modules.objectdetection.object_detection import object_detection
import base64


FILE_CLASSES_NAME = os.environ["FILE_CLASSES_NAME"]
FILE_CONFIG_NAME = os.environ["FILE_CONFIG_NAME"]
FILE_WEIGHTS_NAME = os.environ["FILE_WEIGHTS_NAME"]

bucket_name = "tcastel-object-detection"

def load_file_content_from_S3(bucket_name, key):
    """Return the content of the file loaded."""

    try:
        file_obj = s3.get_object(Bucket=bucket_name, Key=key)
        file_content = file_obj["Body"].read()
        return file_content

    except Exception as e:
        print(e)
        print("""Error getting object {} in the bucket {}. Make sure they
                exist and your bucket is in the
                same region as this function.""".format(key, bucket_name))
        raise e

def read_image_from_S3(bucket_name, key):
    """Return the matrice of the image."""
    
    file_content = load_file_content_from_S3(bucket_name, key)
    print("!!!!!!!!!!!!!!!")
    print(file_content)
    np_array = np.frombuffer(file_content, np.uint8)
    return cv2.imdecode(np_array, cv2.IMREAD_COLOR)

def read_image_from_API_Gateway(body):
    """Return the matrice of the image."""
    decoded_body = base64.b64decode(body)
    print(decoded_body)
    np_array = np.frombuffer(decoded_body, np.uint8)
    return cv2.imdecode(np_array, cv2.IMREAD_COLOR)

def download_temporary_file_from_S3(bucket_name, key):
    """Download a file from S3 and return the filename."""

    localFilename = '/tmp/{}'.format(os.path.basename(key))

    if os.path.exists(localFilename):
        return localFilename
    else:
        try:
            s3.download_file(
                Bucket=bucket_name,
                Key=key,
                Filename=localFilename)

            return localFilename
        except Exception as e:
            print(e)
            print("""Error downloading  object {} in the bucket {}.
            Make sure they exist and your bucket is in the same
            region as this function."""
                  .format(key, bucket_name))
            raise e


def load_model_classes_from_S3(bucket_name, key):
    """Return a list with all the classes detected by the model"""

    file_classes = load_file_content_from_S3(bucket_name, key)
    return file_classes.decode("utf-8").split("\n")


s3 = boto3.client('s3')


def lambda_handler(event, context):

    body = event["body"]

#   Read image and prepare classes
    
    image = read_image_from_API_Gateway(body)
    
    classes = load_model_classes_from_S3(
        bucket_name, "models/" + FILE_CLASSES_NAME)

#   Load model
    localFilename_cfg = download_temporary_file_from_S3(
        bucket_name,
        "models/" + FILE_CONFIG_NAME)

    localFilename_weights = download_temporary_file_from_S3(
        bucket_name,
        "models/" + FILE_WEIGHTS_NAME)

#   Detect objects in an image write the detection on the image
    object_detection(image, classes, localFilename_weights, localFilename_cfg)

#   Create a new key for the image

     # Write grayscale image to /tmp
    cv2.imwrite("/tmp/detected.jpg", image)
    
    # Convert grayscale image into utf-8 encoded base64
    with open("/tmp/detected.jpg", "rb") as imageFile:
      str = base64.b64encode(imageFile.read())
      encoded_img = str.decode("utf-8")

    return {
      "isBase64Encoded": True,
      "statusCode": 200,
      "headers": { "content-type": "image/jpeg"},
      "body":  encoded_img
    }


    """
    try:

        response = s3.put_object(
            Body=cv2.imencode('.jpg', image)[1].tostring(),
            Bucket=bucket_name,
            Key=new_key)

        return response
    """