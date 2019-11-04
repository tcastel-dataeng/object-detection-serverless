#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#

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
from objectdetection import object_detection


FILE_CLASSES_NAME = os.environ["FILE_CLASSES_NAME"]
FILE_CONFIG_NAME = os.environ["FILE_CONFIG_NAME"]
FILE_WEIGHTS_NAME = os.environ["FILE_WEIGHTS_NAME"]


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
    raise


def read_image_from_S3(bucket_name, key):
    """Return the matrice of the image."""

    file_content = load_file_content_from_S3(bucket_name, key)
    np_array = np.frombuffer(file_content, np.uint8)
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


def download_temporary_file_from_S3_bis(bucket_name, key):

    localFilename = '/tmp/{}'.format(os.path.basename(key))
    f = tempfile.NamedTemporaryFile(delete=False)
    f.write(load_file_content_from_S3(bucket_name, key))

    return f.name


def load_model_classes_from_S3(bucket_name, key):
    """Return a list with all the classes detected by the model"""

    file_classes = load_file_content_from_S3(bucket_name, key)
    return file_classes.decode("utf-8").split("\n")


s3 = boto3.client('s3')


def lambda_handler(event, context):

    #   print("Received event: " + json.dumps(event, indent=2))

    #   Get the object from the event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse\
                .unquote_plus(
                    event['Records'][0]['s3']['object']['key'],
                    encoding='utf-8')

#   Read image and prepare classes
    image = read_image_from_S3(bucket_name, key)
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
    filename, file_extension = os.path.splitext(key)
    new_key = "transformedImages/" + filename[7:] +\
        "ObjectDetection" + file_extension

    try:

        response = s3.put_object(
            Body=cv2.imencode('.jpg', image)[1].tostring(),
            Bucket=bucket_name,
            Key=new_key)

        return response
    except Exception as e:
        print(e)
        print("""Error put in object {} in the bucket {}. Make sure they
        exist and your bucket is in the same region as this function."""
              .format(key, bucket_name))
        raise e
