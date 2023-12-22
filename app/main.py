import os
import boto3
from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Union
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

region = os.getenv('DB_REGION_NAME')
access_key_id = os.getenv('DB_ACCESS_KEY_ID')
secret_access_key = os.getenv('DB_SECRET_ACCESS_KEY')

# Initialize a DynamoDB client
dynamodb = boto3.resource(
    'dynamodb',
    region_name=region,
    aws_access_key_id=access_key_id,
    aws_secret_access_key=secret_access_key
)

# SNS call
os.environ['AWS_ACCESS_KEY_ID'] = 'AKIA5G5LLVRWR7HS3YVA'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'tYGIg9Sgtu4w441XaGlnQoZ1HpLpdNPXQkwq7yRB'
# Create an SNS client
sns = boto3.client('sns', region_name='us-east-1')



# Reference to your DynamoDB table
table = dynamodb.Table('document')


class Document(BaseModel):
    document_id: str
    create_time: str
    owner: str
    document_name: str
    content: str
    viewers: list[str]


class UpdateDocument(BaseModel):
    content: Union[str, None] = None
    viewers: Union[List[str], None] = None

@app.post("/documents/")
def create_document(document: Document):
    try:
        response = table.put_item(
            Item={
                'documentId': document.document_id,
                'CreateTime': document.create_time,
                'Owner': document.owner,
                'DocumentName': document.document_name,
                'Content': document.content,
                'Viewers': document.viewers
            }
        )
        return response
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents/{document_id}/{create_time}")
def read_document(document_id: str, create_time: str):
    try:
        response = table.get_item(
            Key={
                'documentId': document_id,
                'CreateTime': create_time
            }
        )
        return response.get('Item')
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/documents/{document_id}/{create_time}")
def update_document(document_id: str, create_time: str, update_data: UpdateDocument):
    try:
        update_expression = "set"
        expression_attribute_values = {}

        if update_data.content is not None:
            update_expression += " Content = :c,"
            expression_attribute_values[':c'] = update_data.content

        if update_data.viewers is not None:
            update_expression += " Viewers = :v"
            expression_attribute_values[':v'] = update_data.viewers

        response = table.update_item(
            Key={
                'documentId': document_id,
                'CreateTime': create_time
            },
            UpdateExpression=update_expression.rstrip(','),
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="UPDATED_NEW"
        )
        
        # Publish a message to the topic
        SNS_response = sns.publish(
            TopicArn='arn:aws:sns:us-east-1:908208090221:MyTestTopic',
            Message='minidocse6156@gmail.com,This is a message from python!'
        )
        return response
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/{document_id}/{create_time}")
def delete_document(document_id: str, create_time: str):
    try:
        response = table.delete_item(
            Key={
                'documentId': document_id,
                'CreateTime': create_time
            }
        )
        return response
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents/")
def read_all_documents(last_evaluated_key: Union[str, None] = None):
    try:
        scan_kwargs = {}
        if last_evaluated_key:
            scan_kwargs['ExclusiveStartKey'] = {
                'documentId': last_evaluated_key}

        response = table.scan(**scan_kwargs)
        items = response.get('Items', [])
        last_evaluated_key = response.get('LastEvaluatedKey')

        return {"items": items, "last_evaluated_key": last_evaluated_key}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

#handle share
@app.get("/share")
def share_document():

    # Send SNS notification
    try:
        sns.publish(
            TopicArn='arn:aws:sns:us-east-1:908208090221:MyTestTopic',
            Message=f'minidocse6156@gmail.com, Document has been shared',
        )
        return {"message": "Document shared and notification sent"}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))
