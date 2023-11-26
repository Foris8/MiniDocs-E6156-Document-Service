import os
import boto3
from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Union
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

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


# Reference to your DynamoDB table
table = dynamodb.Table('document')

class Document(BaseModel):
    document_id: str
    create_time: str
    content: str

@app.post("/documents/")
def create_document(document: Document):
    try:
        response = table.put_item(
            Item={
                'documentId': document.document_id,
                'CreateTime': document.create_time,
                'content': document.content
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
def update_document(document_id: str, create_time: str, content: Union[str, None] = None):
    try:
        response = table.update_item(
            Key={
                'documentId': document_id,
                'CreateTime': create_time
            },
            UpdateExpression="set content = :c",
            ExpressionAttributeValues={
                ':c': content
            },
            ReturnValues="UPDATED_NEW"
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
    
