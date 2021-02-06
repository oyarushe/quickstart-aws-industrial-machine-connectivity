import os
import logging
from datetime import datetime

import boto3

from createSitewiseResources import CreateSitewiseResources
from sitewiseUtils import SitewiseUtils

log = logging.getLogger('assetModelConverter')
log.setLevel(logging.DEBUG)


def handler(event, context):
    sitewise = boto3.client('iotsitewise')
    dynamodb = boto3.client('dynamodb')
    tableName = os.environ['StatusTable']

    log.info('Processing Event {}'.format(event))
    CreateSitewiseResources().processEvent(event)

    # Re-deploy SiteWise Gateway to recognize new tags
    sitewiseUtils = SitewiseUtils()
    gatewayID = sitewiseUtils.getGatewayIDByName()
    sitewiseUtils.updateGateway(gatewayID)    

    # Write to DynamoDB indicating status
    now = datetime.now()
    dynamodb.put_item(
        TableName=tableName,
        Item={'amcStatus':{'S':"Models/Assets Created"},"timestamp":{'S': now.strftime(now.strftime('%b-%d-%Y %H:%M:%S'))}}
    )
