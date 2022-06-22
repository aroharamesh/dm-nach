import json
import os
import boto3


# Function to convert bytes from the api response to dict
def response_to_dict(response):
    response_content = response.content
    response_decode = response_content.decode("UTF-8")
    json_acceptable_string = response_decode.replace("'", '"')
    convert_to_json = json.loads(json_acceptable_string)
    response_dict = dict(convert_to_json)
    return response_dict


# Function to download file from s3 bucket
def download_from_s3():
    s3 = boto3.resource("s3")
    bucket = "aleentapublicimages"

    path = "images"
    if not os.path.exists(path):
        os.makedirs(path)

    s3.Object(bucket, "images/fastapi/1.jpg").download_file(path + "1.jpg")
