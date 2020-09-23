import json
import logging
import os
import time

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError


log = logging.getLogger('assetModelConverter')
log.setLevel(logging.DEBUG)


class KepserverFileDriver:
    def __init__(self):
        self.boto3_session = boto3.Session()
        self.dynamo_client = self.boto3_session.resource('dynamodb')
        self.asset_model_table = self.dynamo_client.Table(os.environ['DynamoDB_Model_Table'])
        self.asset_table = self.dynamo_client.Table(os.environ['DynamoDB_Asset_Table'])

    def get_model_array(self, model_file_data):
        model_array = []
        # Get Project info
        node = {
            "assetModelName": "__Project",
            "parent": "root",
            "assetModelProperties": [],
            "assetModelHierarchies": [],
            "change": 'YES'
        }
        model_array.append(node)
        node = {
            "assetModelName": "__Channel",
            "parent": "__Project",
            "assetModelProperties": [],
            "assetModelHierarchies": [],
            "change": 'YES'
        }
        model_array.append(node)
        for channel in model_file_data['project']['channels']:
            for device in channel['devices']:
                node = {
                    "assetModelName": device['common.ALLTYPES_NAME'],
                    "parent": "__Channel",
                    "assetModelProperties": [],
                    "assetModelHierarchies": [],
                    "change": 'YES'
                }
                for tag in device['tags']:
                    tagType = None
                    if tag['servermain.TAG_DATA_TYPE'] == 8:
                        tagType = 'DOUBLE'
                    if tag['servermain.TAG_DATA_TYPE'] == 1:
                        tagType = 'BOOLEAN'
                    if tagType is not None:
                        tag = {
                            "name": tag['common.ALLTYPES_NAME'],
                            "dataType": tagType,
                            "type": {
                                "measurement": {}
                            }
                        }
                        node['assetModelProperties'].append(tag)
                model_array.append(node)
        return model_array

    def get_asset_array(self, model_file_data):
        asset_array = []
        # Get Project info
        node = {
            "assetName": model_file_data['project']['servermain.PROJECT_TITLE'],
            "modelName": "__Project",
            'change': 'YES'
        }
        asset_array.append(node)
        for channel in model_file_data['project']['channels']:
            channel_name = channel['common.ALLTYPES_NAME']
            node = {
                'assetName': channel_name,
                'modelName': '__Channel',
                'parentName': model_file_data['project']['servermain.PROJECT_TITLE'],
                'change': 'YES'
            }
            asset_array.append(node)
            for device in channel['devices']:
                device_name = device['common.ALLTYPES_NAME']
                node = {
                    'assetName': device_name,
                    'modelName': device_name,
                    'parentName': channel_name,
                    'change': 'YES',
                    'tags': []
                }
                for tag in device['tags']:
                    tag_name = tag['common.ALLTYPES_NAME']
                    tag_path = '/'+channel_name+'/'+device_name+'/'+tag_name
                    tag = {
                        'tagName': tag_name,
                        'tagPath': tag_path
                    }
                    node['tags'].append(tag)
                asset_array.append(node)
        return asset_array

    def createDynamoRecords(self, table, data, primaryKey):
        for record in data:
            try:
                table.put_item(Item=record, ConditionExpression=f'attribute_not_exists({primaryKey})')
                time.sleep(0.1)

            except ClientError as cErr:
                if cErr.response['Error']['Code'] == 'ConditionalCheckFailedException':
                    log.info('Ignoring existing record {}'.format(record[primaryKey]))
                else:
                    raise

    def processEvent(self, event):
        model_file_data = event['birthData']

        for model in model_file_data:
            # Model Creation
            model_array = self.get_model_array(model)
            self.createDynamoRecords(self.asset_model_table, model_array, 'assetModelName')

            # Asset Creation
            asset_array = self.get_asset_array(model)
            self.createDynamoRecords(self.asset_table, asset_array, 'assetName')


def handler(event, context):
    KepserverFileDriver().processEvent(event)


