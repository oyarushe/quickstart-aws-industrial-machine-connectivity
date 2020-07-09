"""
CfnResponse, modified from the original AWS version. This is reponsible for making sure that a proper success/failure
message is sent to cloudformation at the end of a custom resource lambda's execution.

** ERRORS IN THIS CODE WILL CAUSE YOUR STACK DEPLOYMENT/UPDATE/DESTRUCTION TO HANG **

Written by Nathan Slawson, 2020
"""
import json
import logging
import time

# from botocore.vendored import requests
import requests

logger = logging.getLogger('cfnGreengrass')
logger.setLevel(logging.INFO)


class CfnResponse:
    """
    Sends success/error responses to Cloudformation for custom resource lambdas.
    """
    def __init__(self, retryLimit=3, retryDelay=10):
        self.retryLimit = retryLimit
        self.retryDelay = retryDelay

    def error(self, event, context, responseData=None, message=None):
        """
        Sends an error event.
        :param event: Lambda event
        :param context: Lambda context
        :param responseData: The responseData contents
        :param message: Error message
        :return:
        """
        if not responseData:
            responseData = {}

        self.send(event, context, responseData, "FAILED", reason=message)

    def send(self, event, context, responseData, responseStatus="SUCCESS", physicalResourceId=None, noEcho=False, reason=None):
        """
        Sends a success event
        :param event: Lambda event
        :param context: Lambda context
        :param responseData: Any data you wish to return as a result of the operations of the custom resource lambda.
        :param responseStatus: Status of the custom resource lambda.
        :param physicalResourceId:
        :param noEcho:
        :param reason:
        :return:
        """
        responseUrl = event['ResponseURL']
        logger.info(responseUrl)

        responseBody = {
            'Status': responseStatus,
            'Reason': reason or ('See the details in CloudWatch Log Stream: ' + context.log_stream_name),
            'PhysicalResourceId': physicalResourceId or context.log_stream_name,
            'StackId': event['StackId'],
            'RequestId': event['RequestId'],
            'LogicalResourceId': event['LogicalResourceId'],
            'NoEcho': noEcho,
            'Data': responseData,
        }

        body = json.dumps(responseBody)
        logger.info("| response body:\n" + body)

        headers = {
            'content-type': '',
            'content-length': str(len(body))
        }

        for retryCount in range(0, self.retryLimit):
            try:
                logger.info('Sending CfnResponse status {}/{}'.format(retryCount+1, self.retryLimit))
                response = requests.put(responseUrl, data=body, headers=headers)
                logger.info("| status code: " + response.reason)

                break
            except Exception as genErr:
                logger.error("| unable to send response to CloudFormation")
                logger.exception(genErr)

            time.sleep(self.retryDelay)