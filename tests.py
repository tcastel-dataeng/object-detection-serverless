import os
import tempfile
import unittest
import boto3
import botocore
from moto import mock_s3
import lambda_function
import json

MY_BUCKET = "my_bucket"
MY_PREFIX = "mock_folder"

@mock_s3
class TestUseS3(unittest.TestCase):
    def setUp(self):
        
        os.mkdir("tmp")
        os.mkdir("tmp/models")
        
        client = boto3.client(
            "s3",
            region_name="us-east-1",
            aws_access_key_id="access_key",
            aws_secret_access_key="secret_key",
            )
        try:
            s3 = boto3.resource(
                "s3",
                region_name="us-east-1",
                aws_access_key_id="access_key",
                aws_secret_access_key="secret_key",
                )
            s3.meta.client.head_bucket(Bucket=MY_BUCKET)
        except botocore.exceptions.ClientError:
            pass
        else:
            err = "{bucket} should not exist.".format(bucket=MY_BUCKET)
            raise EnvironmentError(err)
        client.create_bucket(Bucket=MY_BUCKET)
        current_dir = os.path.dirname(__file__)
        fixtures_dir = os.path.join(current_dir, MY_PREFIX)
        _upload_fixtures(MY_BUCKET, fixtures_dir)

    
    def tearDown(self):

        os.rmdir("tmp/models")
        os.rmdir("tmp")
        
        s3 = boto3.resource(
            "s3",
            region_name="us-east-1",
            aws_access_key_id="access_key",
            aws_secret_access_key="secret_key",
            )
        bucket = s3.Bucket(MY_BUCKET)
        for key in bucket.objects.all():
            key.delete()
        bucket.delete()
    
    def test_load_file_content_from_S3(self):
        testContent = lambda_function.load_file_content_from_S3(MY_BUCKET,"test.txt")
        self.assertEqual(testContent.decode("utf-8"),"test")
    
    def test_download_files_from_S3(self):
        filename = lambda_function.download_temporary_file_from_S3(MY_BUCKET,"test.txt")
        with open(filename) as file:
            testContent = file.read()
            self.assertEqual(testContent,"test")

    def test_run_main(self):

        with open('testEvent.json', 'r') as test_event_file:
            event = json.load(test_event_file)

        response = lambda_function.lambda_handler(event,0)
        self.assertEqual(response["ResponseMetadata"]["HTTPStatusCode"],200)
    


def _upload_fixtures(bucket: str, fixtures_dir: str) -> None:
        client = boto3.client("s3")
        fixtures_paths = [
            os.path.join(path,  filename)
            for path, _, files in os.walk(fixtures_dir)
            for filename in files
        ]
        for path in fixtures_paths:
            key = os.path.relpath(path, fixtures_dir)
            client.upload_file(Filename=path, Bucket=bucket, Key=key)
    

if __name__ == "__main__":
    unittest.main()