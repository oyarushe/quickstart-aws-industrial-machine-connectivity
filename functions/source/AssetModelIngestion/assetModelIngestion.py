import datetime
import json
import logging
import os
import pprint
import tempfile
import uuid

from s3Utils import S3Utils

import boto3
from boto3.s3.transfer import TransferConfig, S3Transfer
from botocore.exceptions import ClientError

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class AssetModelIngestion:
    def __init__(self):
        self.s3Utils = S3Utils(os.environ['IncomingBucket'])

        self.timestampFormat = '%Y-%m-%d_%H-%M-%S'

    def processEvent(self, event):
        log.info(pprint.pformat(event, indent=4))

        with tempfile.TemporaryDirectory() as dataDir:
            currDateTime = datetime.datetime.utcnow().strftime(self.timestampFormat)
            s3Filename = os.path.join(dataDir, '{}_{}.json'.format(currDateTime, uuid.uuid4()))

            with open(s3Filename, 'w', encoding='utf-8') as tempFile:
                tempFile.write(json.dumps(event, indent=4))

            self.s3Utils.uploadFile(s3Filename)


def handler(event, context):
    myClass = AssetModelIngestion()
    myClass.processEvent(event)

