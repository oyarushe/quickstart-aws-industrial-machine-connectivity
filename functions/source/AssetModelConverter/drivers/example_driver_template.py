import logging
import os
import time

import boto3
from botocore.exceptions import ClientError


log = logging.getLogger('assetModelConverter')
log.setLevel(logging.DEBUG)


class ExampleDriverTemplate:
    def __init__(self):
        self.boto3_session = boto3.Session()
        self.dynamoClient = self.boto3_session.resource('dynamodb')
        self.assetModelTable = self.dynamoClient.Table(os.environ['DynamoDB_Model_Table'])
        self.assetTable = self.dynamoClient.Table(os.environ['DynamoDB_Asset_Table'])

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
        # event['birthData'] contains a list[] of ingested model files, loaded as JSON into python dictionary form.
        # Your edge software may produce one or more of these model files, and they should all be presented to you here.
        modelFileData = event['birthData']

        # From here, process the modelFileData, and then populate the self.assetModelTable and self.assetTable
        # dynamoDB tables. Please see the 'Getting Started' guide for documentation on this format, or reference the
        # example Ignition and/or KepServer drivers.


def handler(event, context):
    ExampleDriverTemplate().processEvent(event)


