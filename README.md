# object-detection-serverless

This Lambda serverless function is triggered by an S3 event when an image is uploaded to an S3. It detect the object on an image and save this prediction in the same S3. 

Prerequites :

- Install serverless framework
- configure your credentials
- create an S3 bucket with the following structure

    YOUR_S3_BUCKET_NAME/
                images/
                models/
                transformedImages/

- Fetch the model configuration and weights from darknet : https://pjreddie.com/darknet/yolo/
    and save them under the models path of your bucket. If you want a quick start you can use the tiny model present in the mockfolder. Although it might not be the most efficient model.

- Add the file of classes into your S3 under the model path (it is also present in the mockfolder directory).

- serverless deploy --bucket_name YOUR_S3_BUCKET_NAME --verbose


Sources and inspirations :