import logging

import boto3

from createSitewiseResources import CreateSitewiseResources
from sitewiseUtils import SitewiseUtils

log = logging.getLogger('assetModelConverter')
log.setLevel(logging.DEBUG)


def handler(event, context):
    sitewise = boto3.client('iotsitewise')

    log.info('Processing Event {}'.format(event))
    CreateSitewiseResources().processEvent(event)

    # Re-deploy SiteWise Gateway to recognize new tags
    sitewiseUtils = SitewiseUtils()
    gatewayID = sitewiseUtils.getGatewayIDByName()
    sitewiseUtils.updateGateway(gatewayID)    
