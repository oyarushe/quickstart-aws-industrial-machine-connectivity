#!/usr/bin/env python3
"""
Asset Model Converter

Written by Nathan Slawson and Shahan Krakirian, 2020
"""
import codecs
import collections.abc
from datetime import date, datetime
import json
import logging
import os
import sys
import tempfile
import time

from s3Utils import S3Utils
from drivers.ignitionCirrusLinkDriver import CirrusLinkDriver
from drivers.kepserver_file_driver import KepserverFileDriver
from drivers.ignitionFileDriver import IgnitionFileDriver
from createSitewiseResources import CreateSitewiseResources

log = logging.getLogger('assetModelConverter')
log.setLevel(logging.DEBUG)


class AssetModelConverter:
    def __init__(self):
        self.s3Utils = S3Utils(os.environ['IncomingBucket'])
        # Time to wait for no change in birth object count in seconds
        self.birthObjectScanTime = int(os.environ.get('OverrideScanTime', 10))
        self.keepBirthObjects = bool(os.environ.get('KeepBirthObjects', False))
        self.driverName = os.environ['DriverName']

        # list of S3 birth object files we're working with
        self.birthObjects = []

        self.driverTable = {
            'IgnitionCirrusLink': CirrusLinkDriver,
            'KepwareFileExport': KepserverFileDriver,
            'IgnitionFileExport': IgnitionFileDriver,
        }

        self.driverClass = self.driverTable[self.driverName]

        self.createSitewiseResources = CreateSitewiseResources()

    def checkForBirthObjects(self):
        """
        Scans the incoming bucket for new birth messages. After they begin to arrive,
        waits until no new birth objects have arrived for birthObjectScanTime in seconds.
        :return:
        """

        lastObjectCount = 0
        lastChangeTime = time.time()

        while True:
            birthObjects = self.s3Utils.listObjects()

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

    def checkForBOM(self, filename):
        with open(filename, 'rb') as binFile:
            rawData = binFile.read(64)
            if rawData.startswith(codecs.BOM_UTF8):
                return True

        return False

    def getBirthData(self):
        """
        Gets all birth objects from the incoming s3 bucket. Combines the structures, storing assets in self.assets
        and models in self.models.
        :return:
        """
        birthData = []

        objectList = self.s3Utils.listObjects()
        with tempfile.TemporaryDirectory() as tempFolder:
            for fileObject in objectList:
                objectFilename = os.path.join(tempFolder, os.path.basename(fileObject['Key']))
                self.s3Utils.downloadFile(fileObject['Key'], objectFilename)

                self.birthObjects.append(fileObject['Key'])

                fileEncoding = 'utf-8'
                if self.checkForBOM(objectFilename):
                    fileEncoding = 'utf-8-sig'

                with open(objectFilename, 'r', encoding=fileEncoding) as bFile:
                    objectData = json.load(bFile)
                    birthData.append(objectData)

                    # cleanedTopic = objectData['topic'].split('/')
                    # cleanedTopic.pop(2)
                    # cleanedTopic.pop(0)
                    # # cleanedTopicString = '/'.join(cleanedTopic)
                    #
                    # for metric in objectData['metrics']:
                    #     # Skipping metrics that are for internal ignition usage
                    #     if type(metric['value']) != dict or metric['value'].get('isDefinition') is None:
                    #         continue
                    #
                    #     # metricFullName = cleanedTopicString + '/' + metric['name']
                    #     # log.info(metricFullName)
                    #     mVal = metric['value']
                    #     if mVal['isDefinition']:
                    #         self.models[metric['name']] = mVal
                    #     else:
                    #         assetPath = cleanedTopic + [metric['name']]
                    #         assetValue = self.buildStructure(assetPath, mVal)
                    #
                    #         self.updateDict(self.assets, assetValue)

        return birthData

    def deleteBirthObjects(self):
        """
        Deletes our birth objects from S3
        :return:
        """
        for objectKey in self.birthObjects:
            self.s3Utils.deleteObject(objectKey)

    def processEvent(self, event):
        if self.checkForBirthObjects():
            birthData = self.getBirthData()

            driver = self.driverClass()
            # driver.processBirthObjects(birthData)
            birthEvent = {
                'birthData': birthData,
            }
            driver.processEvent(birthEvent)

            if not self.keepBirthObjects:
                self.deleteBirthObjects()

            self.createSitewiseResources.processEvent(event={})


def handler(event, context):
    """
    Lambda Handler
    :param event:
    :param context:
    :return:
    """
    assetModelClass = AssetModelConverter()
    assetModelClass.processEvent(event)


if __name__ == '__main__':
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s - %(message)s')
    consoleHandler.setFormatter(formatter)
    log.addHandler(consoleHandler)

    customEvent = {}

    os.environ['OverrideScanTime'] = '1'
    os.environ['KeepBirthObjects'] = 'Yes'
    os.environ['SaveAMCData'] = 'Yes'
    os.environ['IncomingBucket'] = 'nathanimcenv-amcincomingresource-11urj0786l9n1'
    # os.environ['DriverName'] = 'IgnitionCirrusLink'
    # os.environ['DriverName'] = 'IgnitionFileExport'
    os.environ['DriverName'] = 'KepwareFileExport'
    os.environ['DynamoDB_Model_Table'] = 'imc_asset_model_table'
    os.environ['DynamoDB_Asset_Table'] = 'imc_asset_table'
    AssetModelConverter().processEvent(customEvent)

