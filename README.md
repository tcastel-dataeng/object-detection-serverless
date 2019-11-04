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

To chose the model :
https://towardsdatascience.com/a-recipe-for-using-open-source-machine-learning-models-within-your-company-1aed833a59b5

For the lambda layer :
https://github.com/keithrozario/Klayers 

About the object detection code :
https://github.com/opencv/opencv/tree/master/samples/dnn
https://www.arunponnusamy.com/yolo-object-detection-opencv-python.html

For the tests :
https://medium.com/@l.peppoloni/how-to-mock-s3-services-in-python-tests-dd5851842946
