#!/usr/bin/env python3
"""
Read kepserver json configuration file from  kepserver_folder and ingest as dataset to Unify
Read ignition json configuration file form ignition_folder and ingest as dataset and templates to Unify
Written by Element Analytics, Inc., 2021
"""

import os
import sys
# unify_scripts/deploy_to_repo.sh copy "unify_common" under the lambda zip package
# for local development, add source folder to python path to import unify_common
package_dir = os.path.dirname(os.path.abspath(__file__))
if (os.path.exists(package_dir + '/local.ini')):
    sys.path.append(os.path.dirname(package_dir))

from unify_common.s3Utils import S3Utils
from unify_common.secrets_manager import SecretsManager

import logging
log = logging.getLogger('unifyAssetModelConverter')
log.setLevel(logging.INFO)

from datetime import date, datetime
import json
import tempfile
import time
import boto3
from ignition_file_agent.agent import Agent as IginitionAgent
from kepserver_file_agent.kepserver_file_agent import KepserverAgent
from utils import parse_file_name, check_for_bom

kepserver_folder = 'KepServerEx/'
ignition_folder = 'Ignition/'

class AssetModelConverter:
    def __init__(self, bucketName):
        self.s3Utils = S3Utils(bucketName)
        # Time to wait for no change in birth object count in seconds
        self.birthObjectScanTime = int(os.environ.get('OverrideScanTime', 5))
        self.keepBirthObjects = bool(os.environ.get('KeepBirthObjects', False))
        self.region_name = os.environ['RegionName']
        self.secret_name = os.environ['SecretName']
        self.append_template_prefix = os.environ.get('AppendTemplatePrefix', False) # Append site_name and server_name on template if Yes
        self.ingestedFiles = []


    def checkForBirthObjects(self, keyPrefix=''):
        """
        Scans the incoming bucket for new birth messages. After they begin to arrive,
        waits until no new birth objects have arrived for birthObjectScanTime in seconds.
        :return:
        """

        lastObjectCount = 0
        lastChangeTime = time.time()

        while True:
            birthObjects = self.s3Utils.listObjectsInFolder(keyPrefix)

            if not birthObjects:
                return False

            if len(birthObjects) == lastObjectCount:
                log.info(f'Found {lastObjectCount} birth objects')
                currTime = time.time()
                if (currTime-lastChangeTime) >= self.birthObjectScanTime:
                    log.info(f'No change found in {self.birthObjectScanTime} seconds, done scanning for birth objects')
                    break
            else:
                lastChangeTime = time.time()
                lastObjectCount = len(birthObjects)

        return lastObjectCount

    def delete_ingested_objects(self):
        for objectKey in self.ingestedFiles:
            self.s3Utils.deleteObject(objectKey)

    def get_file_data(self, temp_folder, s3_file):
        try:
            temp_file = os.path.join(temp_folder, os.path.basename(s3_file))
            self.s3Utils.downloadFile(s3_file, temp_file)
    
            fileEncoding = 'utf-8'
            if check_for_bom(temp_file):
                fileEncoding = 'utf-8-sig'

            with open(temp_file, 'r', encoding=fileEncoding) as bFile:
                object_data = json.load(bFile)
        except Exception as error:
            log.error("Failed to read file data %s, error: %s", s3_file, error)
            raise error
        return object_data

    def process_folder(self, keyPrefix, secret):
        if (keyPrefix == ignition_folder):
            agent = IginitionAgent(secret.user_id, secret.password, secret.org_id, secret.cluster, False, True)
        elif (keyPrefix == kepserver_folder):
            agent = KepserverAgent(secret.user_id, secret.password, secret.org_id, secret.cluster, False, True)
        else:
            raise Exception('Does not support folder %s', keyPrefix)
    
        if self.checkForBirthObjects(keyPrefix):
            objectList = self.s3Utils.listObjectsInFolder(keyPrefix)
            type_laebl = "kepserverex" if keyPrefix == kepserver_folder else "ignition"

            with tempfile.TemporaryDirectory() as temp_folder:
                for fileObject in objectList:
                    s3_file = fileObject['Key']
                    site_name, server_name, file_name = parse_file_name(s3_file)
                    labels = list(set([
                        site_name,
                        server_name,
                        file_name,
                        type_laebl,
                        'imc'
                    ]))
                    object_data  = self.get_file_data(temp_folder, s3_file)
                    if (keyPrefix == ignition_folder):
                        agent.ingest([object_data], site_name, server_name, self.append_template_prefix, labels)
                    elif (keyPrefix == kepserver_folder):
                        agent.ingest([object_data], site_name, server_name, labels)
                    else:
                        raise Exception('Does not support folder %s', keyPrefix)
                    log.info("Ingested file %s, site_name %s, server_name %s", s3_file, site_name, server_name)
                    self.ingestedFiles.append(s3_file) 

      
    
    def process(self):
        """
        Ingest kepserver tags under 'KepServerEx/', Ignition tags under 'Ignition/'
        Delete files if ingest successfully. Leave the file in the s3 buckey if ingest fails.
        """
        secret_manager = SecretsManager(self.region_name, self.secret_name)
        try:
            secret = secret_manager.get_value()
        except Exception as error:
            log.error('Failed to get secret %s', error)
            raise error

        self.process_folder(kepserver_folder, secret)
        self.process_folder(ignition_folder, secret)

        if not self.keepBirthObjects:
            self.delete_ingested_objects()

   

def lambda_handler(event, context):
    """
    Lambda Handler
    :param event:
    :param context:
    :return:
    """
    log.info('Processing Event {}'.format(event))
    bucketName = event['Records'][0]['s3']['bucket']['name']
    assetModelClass = AssetModelConverter(bucketName)
    assetModelClass.process()


# For testing purposes
if __name__ == '__main__':
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s - %(message)s')
    consoleHandler.setFormatter(formatter)
    log.addHandler(consoleHandler)

    incomming_bucket = 'mary-imc-test-data'

    os.environ['OverrideScanTime'] = '1'
    os.environ['KeepBirthObjects'] = 'Yes'
    os.environ['RegionName'] = 'us-east-1'
    os.environ['SecretName'] = ''
    os.environ['AppendTemplatePrefix'] = 'Yes'
    AssetModelConverter(incomming_bucket).process()
