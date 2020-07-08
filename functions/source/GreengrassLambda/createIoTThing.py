"""
Custom Resource Lambda that manages the IoT Thing in the stack for a given adapterID.

Written by Nathan Slawson, 2020
"""
import json
import logging
import os
import subprocess
import sys
import tempfile

import boto3
from botocore.exceptions import ClientError
from boto3.s3.transfer import TransferConfig, S3Transfer
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger('cfnGreengrass')
logger.setLevel(logging.INFO)


class CreateIoTThing:
    """
    Creates and packages IoT/Greengrass resources like certs, keys, and config files. Uploads those artifacts to S3.
    """
    def __init__(self, stackName, thingName, gatewayID):
        self.stackName = stackName
        self.thingName = thingName
        self.gatewayID = gatewayID

        self.bucketName = os.environ['DevicesBucket']
        self.rootCert = 'https://www.amazontrust.com/repository/AmazonRootCA1.pem'
        self.ggConfigTemplate = 'ggConfigTemplate.json'

        self.s3 = boto3.client('s3')
        self.s3Config = TransferConfig(
            multipart_threshold=1024 * 25,
            max_concurrency=10,
            multipart_chunksize=1024 * 25,
            use_threads=True
        )
        self.s3Transfer = S3Transfer(client=self.s3, config=self.s3Config)
        self.session = boto3.Session()

    def uploadFile(self, fileName, keyPrefix):
        """
        Uploads a file to the configured S3 bucket.
        :param fileName: local filename to upload
        :param keyPrefix: 'Folder' prefix used to build final S3 key path.
        :return:
        """
        try:
            baseName = os.path.basename(fileName)
            s3KeyPath = "{}/{}".format(keyPrefix, baseName)
            logger.info('Uploading {filename} to s3://{bucket}/{key}'.format(
                filename=fileName,
                bucket=self.bucketName,
                key=s3KeyPath
            ))
            self.s3Transfer.upload_file(
                fileName,
                self.bucketName,
                s3KeyPath
            )

        except ClientError:
            logger.exception('Upload of {} failed'.format(fileName))

    @staticmethod
    def readFile(filename):
        """
        Ease of use function to read a file
        :param filename: Filename to read
        :return:
        """
        with open(filename, 'r', encoding='utf-8') as inputFile:
            return inputFile.read()

    @staticmethod
    def writeFile(filename, data):
        """
        Ease of use function to write a file
        :param filename: Filename to write to
        :param data: Contents of the file to write
        :return:
        """
        print('Creating {}'.format(filename))
        with open(filename, 'w', encoding='utf-8') as outputFile:
            outputFile.write(data)

    @staticmethod
    def execCmd(params, cwd=None):
        """
        Ease of use fucntion for executing a command with subprocess
        :param params: List[] of parameters
        :param cwd: current working directory use
        :return:
        """
        myProc = subprocess.run(params, stderr=subprocess.STDOUT, shell=True, cwd=cwd)
        if myProc.returncode != 0:
            raise RuntimeError("Exec failure: {}".format(params))

    def uploadConfigPackage(self, responseData):
        """
        Uses the response data to write cert/key/config files. Packages those files, and uploads them to S3.
        :param responseData:
        :return:
        """
        with tempfile.TemporaryDirectory() as dataDir:
            logger.info('Creating Certs and Config folders')
            certsFolder = os.path.join(dataDir, 'certs')
            os.mkdir(certsFolder)

            folderList = []

            logger.info('Generating pem and key files')
            coreCertData = {
                '{}/{}.pem'.format(certsFolder, responseData['certificateId']): responseData['certificatePem'],
                '{}/{}.key'.format(certsFolder, responseData['certificateId']): responseData['privateKey'],
            }

            for filename, data in coreCertData.items():
                self.writeFile(filename, data)

            logger.info('Grabbing root cert')
            self.execCmd(
                'curl {} -o {}'.format(self.rootCert, os.path.join(certsFolder, 'root.ca.pem'))
            )
            folderList.append('certs')

            # If this thingname ends with 'Core', we assume it's a greengrass core device. If so, it needs a config file.
            if self.thingName.endswith('Core'):
                configFolder = os.path.join(dataDir, 'config')
                os.mkdir(configFolder)

                logger.info('Generating config file')
                j2Env = Environment(loader=FileSystemLoader(os.getcwd()))
                myTemplate = j2Env.get_template(self.ggConfigTemplate)

                responseData['region'] = self.session.region_name
                self.writeFile(os.path.join(configFolder, 'config.json'), myTemplate.render(responseData))
                folderList.append('config')

            logger.info('Packaging and uploading')
            #tarballFilename = '{}_{}.tar.gz'.format(self.thingName, responseData['certificateId'][0:10])
            tarballFilename = '{}.tar.gz'.format(self.thingName)
            # self.execCmd('tar czf {} certs config'.format(tarballFilename), cwd=dataDir)
            self.execCmd('tar czf {} {}'.format(tarballFilename, ' '.join(folderList)), cwd=dataDir)

            self.uploadFile(os.path.join(dataDir, tarballFilename), self.gatewayID)

    def handleEvent(self, event):
        """
        Handles an IoT thing event. This is our main entry point into this class. Creates our keys and certs, and
        some Greengrass related config entries into the responseData. Then calls self.uploadConfigPackage to handle
        packaging and uploading those artifacts to S3.

        Also handles updates(no-op), and deletion of the certs/keys/etc.
        :param event: Lambda event data.
        :return:
        """
        responseData = {}

        logger.info('Received event: {}'.format(json.dumps(event)))
        client = boto3.client('iot')
        # thingName = event['ResourceProperties']['ThingName']

        if event['RequestType'] == 'Create':
            thing = client.create_thing(
                thingName=self.thingName
            )
            response = client.create_keys_and_certificate(
                setAsActive=True
            )
            certId = response['certificateId']
            certArn = response['certificateArn']
            certPem = response['certificatePem']
            privateKey = response['keyPair']['PrivateKey']
            client.create_policy(
                policyName='{}-full-access'.format(self.thingName),
                policyDocument=json.dumps(self.getPolicyDocument())
            )
            response = client.attach_policy(
                policyName='{}-full-access'.format(self.thingName),
                target=certArn
            )
            response = client.attach_thing_principal(
                thingName=self.thingName,
                principal=certArn,
            )
            logger.info('Created thing: %s, cert: %s and policy: %s' %
                        (self.thingName, certId, '{}-full-access'.format(self.thingName)))
            responseData['certificateId'] = certId
            responseData['certificateArn'] = certArn
            responseData['certificatePem'] = certPem
            responseData['thingArn'] = thing['thingArn']
            responseData['privateKey'] = privateKey
            responseData['iotEndpoint'] = client.describe_endpoint(endpointType='iot:Data-ATS')['endpointAddress']

            self.uploadConfigPackage(responseData)

        elif event['RequestType'] == 'Update':
            logger.info('Updating thing: %s' % self.thingName)

            thing = client.describe_thing(thingName=self.thingName)
            responseData['thingArn'] = thing['thingArn']

            principalData = client.list_thing_principals(
                thingName=self.thingName
            )
            responseData['certificateArn'] = principalData['principals'][0]

            logger.info('responseData {}'.format(responseData))

        elif event['RequestType'] == 'Delete':
            logger.info('Deleting thing: %s and cert/policy' % self.thingName)

            try:
                response = client.list_thing_principals(
                    thingName=self.thingName
                )
                for pRef in response['principals']:
                    # arn:aws:iot:us-west-2:129947082896:cert/2b68165653b2e05ef04a3f75cc56bc73bf9a5ecf38408f38dbe116be51120836
                    pData, pIdent = pRef.split('/')
                    arnStr, awsStr, serviceName, regionName, accountID, pType = pData.split(':')

                    logger.info('Deleting principal {}'.format(pRef))
                    response = client.detach_thing_principal(
                        thingName=self.thingName,
                        principal=pRef
                    )

                    if pType == 'cert':
                        response = client.detach_policy(
                            policyName='{}-full-access'.format(self.thingName),
                            target=pRef
                        )
                        response = client.update_certificate(
                            certificateId=pRef.split('/')[-1],
                            newStatus='INACTIVE'
                        )
                        response = client.delete_certificate(
                            certificateId=pRef.split('/')[-1],
                            forceDelete=True
                        )
                        response = client.delete_policy(
                            policyName='{}-full-access'.format(self.thingName),
                        )
                        response = client.delete_thing(
                            thingName=self.thingName
                        )

            except ClientError as cError:
                logger.exception(cError)

        return responseData

    def getPolicyDocument(self):
        """
        Our basic policy for wildcard greengrass/IoT access.
        :return:
        """
        return {
            'Version': '2012-10-17',
            'Statement': [
                {
                  'Effect': 'Allow',
                  'Action': 'iot:*',
                  'Resource': '*'
                },
                {
                  'Effect': 'Allow',
                  'Action': 'greengrass:*',
                  'Resource': '*'
                }
            ]
        }

