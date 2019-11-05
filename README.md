# object-detection-serverless

This Lambda serverless function is triggered by an S3 event when an image is uploaded to an S3. It detects the object on an image and save this prediction in the same S3. 

<h1>Prerequisites :</h1>

- Install serverless framework 
- configure your AWS credentials 
- create an S3 bucket with the following structure

    ```
    YOUR_S3_BUCKET_NAME/
                    ├─ images/                
                    ├─ models/                  
                    └─ transformedImages/
    ```
   
- Fetch the model configuration and weights from darknet : https://pjreddie.com/darknet/yolo/ and save them under the models path of your bucket. If you want a quick start you can use the tiny model present in the mock_folder (situated in the modules/tests directory). Although it might not be the most efficient model.

- Add the file of classes into your S3 under the model path (it is also present in the mockfolder directory as yolov3.txt).

<h1>Get started :</h1>


- Enter the project directory : `$ serverless deploy --bucket_name YOUR_S3_BUCKET_NAME --verbose`
- Put an image (.jpg) to your S3 bucket
- The transformed image will appear in the transformedImage directory of your bucket

<h1>Tests :</h1>

- Enter the project directory and create a new virtualenv : `$ virtualenv venv`
- `$ source venv/bin/activate`
- Use the requirements.txt to install dependencies :`$ pip install -r requirements.txt`
- `$ python3 -m modules.tests.tests -v`

<h1>Sources and inspirations :</h1>

To chose the model :
https://towardsdatascience.com/a-recipe-for-using-open-source-machine-learning-models-within-your-company-1aed833a59b5

For the lambda layer :
https://github.com/keithrozario/Klayers 

About the object detection code :
https://github.com/opencv/opencv/tree/master/samples/dnn

https://www.arunponnusamy.com/yolo-object-detection-opencv-python.html

https://github.com/arunponnusamy/object-detection-opencv

For the tests :
https://medium.com/@l.peppoloni/how-to-mock-s3-services-in-python-tests-dd5851842946
