"""
Greengrass related custom resource event handler

Written by Nathan Slawson, 2020
"""
import json
import logging
import sys

from cfnResponse import CfnResponse
from manageGreengrass import ManageGreengrass
from createIoTThing import CreateIoTThing

log = logging.getLogger('cfnGreengrass')
log.setLevel(logging.INFO)

# consoleHandler = logging.StreamHandler(sys.stdout)
# consoleHandler.setLevel(logging.INFO)
# formatter = logging.Formatter('%(asctime)s %(levelname)s - %(message)s')
# consoleHandler.setFormatter(formatter)
# log.addHandler(consoleHandler)


def handler(event, context):
    """
    Out event handler. This decides what type of event type it is, and calls the appropriate event in the related class.
    :param event: Lambda event
    :param context: Lambda context
    :return:
    """
    try:
        log.info(json.dumps(event, indent=4))
        resourceProps = event['ResourceProperties']

        responseData = {}

        stackName = resourceProps['StackName']
        eventType = resourceProps['EventType']

        if eventType == 'CreateIoTThing':
            thingName = event['ResourceProperties']['ThingName']
            gatewayID = event['ResourceProperties']['GatewayID']
            responseData = CreateIoTThing(stackName=stackName, thingName=thingName, gatewayID=gatewayID).handleEvent(event)

        elif eventType == 'ManageGreengrass':
            responseData = ManageGreengrass(stackName=stackName).handleEvent(event)

        CfnResponse().send(event, context, responseData=responseData)

        return

    except Exception as genErr:
        log.exception(genErr)

    CfnResponse().error(event, context)
