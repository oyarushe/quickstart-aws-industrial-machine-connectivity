import datetime
import json
import logging
import os
import pprint
import tempfile
import uuid

import boto3
from boto3.s3.transfer import TransferConfig, S3Transfer
from botocore.exceptions import ClientError

log = logging.getLogger('assetModelConverter')
log.setLevel(logging.DEBUG)


class S3Utils:
    def __init__(self, bucket):
        self.bucketName = bucket

        self.s3 = boto3.client('s3')
        self.s3Config = TransferConfig(
            multipart_threshold=1024 * 25,
            max_concurrency=10,
            multipart_chunksize=1024 * 25,
            use_threads=True
        )
        self.s3Transfer = S3Transfer(client=self.s3, config=self.s3Config)
        self.session = boto3.Session()

    def listObjects(self, keyPrefix=''):
        try:
            log.info('Listing objects s3://{}/{}'.format(self.bucketName, keyPrefix))

            objectList = []

            paginator = self.s3.get_paginator('list_objects')
            pageIterator = paginator.paginate(Bucket=self.bucketName, Prefix=keyPrefix)

            for page in pageIterator:
                # log.info(page['Contents'])
                if 'Contents' in page:
                    for fileObject in page['Contents']:
                        objectList.append(fileObject)

            return objectList

        except ClientError:
            log.exception('Failed to listObjects {}'.format(keyPrefix))
    
    def listObjectsInFolder(self, keyPrefix=''):
        try:
            log.info('Listing objects s3://{}/{}'.format(self.bucketName, keyPrefix))

            objectList = []

            paginator = self.s3.get_paginator('list_objects')
            pageIterator = paginator.paginate(Bucket=self.bucketName, Prefix=keyPrefix)

            for page in pageIterator:
                # log.info(page['Contents'])
                if 'Contents' in page:
                    for fileObject in page['Contents']:
                        if fileObject['Key'] != keyPrefix:
                            objectList.append(fileObject)

            return objectList

        except ClientError:
            log.exception('Failed to listObjects {}'.format(keyPrefix))

    def deleteObject(self, key):
        log.info(f'Deleting object s3://{self.bucketName}/{key}')
        self.s3.delete_object(Bucket=self.bucketName, Key=key)

    def uploadFile(self, filename, keyPrefix=None):
        """
        Uploads a file to the configured S3 bucket.
        :param filename: local filename to upload
        :param keyPrefix: 'Folder' prefix used to build final S3 key path.
        :return:
        """
        try:
            baseName = os.path.basename(filename)
            if keyPrefix:
                s3KeyPath = "{}/{}".format(keyPrefix, baseName)
            else:
                s3KeyPath = baseName

            log.info('Uploading {filename} to s3://{bucket}/{key}'.format(
                filename=filename,
                bucket=self.bucketName,
                key=s3KeyPath
            ))
            self.s3Transfer.upload_file(
                filename,
                self.bucketName,
                s3KeyPath
            )

        except ClientError:
            log.exception('Upload of {} failed'.format(filename))

    def downloadFile(self, key, filename):
        try:
            log.info('Downloading s3://{bucket}/{key} to {filename}'.format(
                filename=filename,
                bucket=self.bucketName,
                key=key
            ))
            self.s3Transfer.download_file(
                bucket=self.bucketName,
                key=key,
                filename=filename
            )

        except ClientError:
            log.exception('Download of {} -> {} failed'.format(key, filename))
