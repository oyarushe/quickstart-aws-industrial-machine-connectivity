#!/usr/bin/env python3
import collections.abc
from datetime import date, datetime
import json
import logging
import os
import re
import sys
import tempfile
import time

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from sitewiseUtils import SitewiseUtils

log = logging.getLogger('assetModelConverter')
log.setLevel(logging.DEBUG)


class CreateSitewiseResources:
    def __init__(self):
        self.iotData = boto3.client('iot-data')
        self.boto3Session = boto3.Session()
        self.dynamo = self.boto3Session.resource('dynamodb')
        self.assetModelTable = self.dynamo.Table(os.environ['DynamoDB_Model_Table'])
        self.assetTable = self.dynamo.Table(os.environ['DynamoDB_Asset_Table'])

        self.completionTopics = [
            'imc/control/sitewisemonitor',
            'imc/control/quicksight',
        ]

        self.sitewiseUtils = SitewiseUtils()

        self.modelList = []
        self.assetList = []

    def getChangedAssets(self):
        response = self.assetTable.query(
            IndexName="change-index",
            KeyConditionExpression=Key('change').eq('YES'),
        )

        return response['Items']

    def getChangedModels(self):
        response = self.assetModelTable.query(
            IndexName="change-index",
            KeyConditionExpression=Key('change').eq('YES'),
        )

        return response['Items']

    def getModelByName(self, name):
        response = self.assetModelTable.get_item(Key={'assetModelName': name})

        return response['Item']

    def getAssetByName(self, name):
        response = self.assetTable.get_item(Key={'assetName': name})

        return response['Item']

    def createModels(self):
        modelList = self.getChangedModels()

        for model in modelList:
            if 'assetModelId' in model:
                continue

            modelDescription = self.sitewiseUtils.createAssetModel(
                modelName=model['assetModelName'],
                modelProperties=model['assetModelProperties'],
                modelHierarchies=model['assetModelHierarchies'],
            )

            model['assetModelId'] = modelDescription['assetModelId']
            model['assetModelArn'] = modelDescription['assetModelArn']
            model['change'] = 'NO'

            self.assetModelTable.put_item(Item=model)

        return modelList

    def createPropertyAlias(self, asset):
        """
        Creates a property alias from the asset node, and updates the relevant sitewise asset with it.
        :param asset:
        :return:
        """
        if asset['assetProperties'] and asset['tags']:
            aliasMap = {}

            for tag in asset['tags']:
                aliasMap[tag['tagName']] = tag['tagPath']

            self.sitewiseUtils.updateAssetProperties(
                assetId=asset['assetId'],
                assetProperties=asset['assetProperties'],
                assetAliases=aliasMap,
            )

    def createAssets(self):
        assetList = self.getChangedAssets()
        for asset in assetList:
            if 'assetId' in asset:
                continue

            assetModelId = self.getModelByName(asset['modelName'])['assetModelId']
            assetDescription = self.sitewiseUtils.createAsset(
                assetName=asset['assetName'],
                assetModelId=assetModelId,
            )

            asset['assetId'] = assetDescription['assetId']
            asset['assetArn'] = assetDescription['assetArn']
            asset['assetProperties'] = assetDescription['assetProperties']
            asset['change'] = 'NO'

            self.assetTable.put_item(Item=asset)

            self.createPropertyAlias(asset)

        return assetList

    def updateAssetModelHierarchies(self):
        for asset in self.assetList:
            if 'parentName' in asset and asset['parentName']:
                myModel = self.getModelByName(asset['modelName'])
                parentAsset = self.getAssetByName(asset['parentName'])
                parentModel = self.getModelByName(parentAsset['modelName'])

                hierMap = {}
                for hierRef in parentModel['assetModelHierarchies']:
                    hierMap[hierRef['name']] = hierRef

                if myModel['assetModelName'] not in hierMap:
                    parentModel['assetModelHierarchies'].append({
                        "name": myModel['assetModelName'],
                        "childAssetModelId": myModel['assetModelId'],
                    })
                    parentModel['change'] = 'YES'

                    self.assetModelTable.put_item(Item=parentModel)

                asset['change'] = 'YES'
                self.assetTable.put_item(Item=asset)

    def updateModels(self):
        modelList = self.getChangedModels()

        for model in modelList:
            if 'assetModelId' not in model:
                continue

            modelDescription = self.sitewiseUtils.updateAssetModel(
                assetModelId=model['assetModelId'],
                assetModelName=model['assetModelName'],
                hierarchies=model['assetModelHierarchies'],
            )

            model['assetModelHierarchies'] = modelDescription['assetModelHierarchies']
            model['change'] = 'NO'
            self.assetModelTable.put_item(Item=model)

    def associateAssets(self):
        assetList = self.getChangedAssets()

        for asset in assetList:
            if 'assetId' not in asset:
                continue

            myModel = self.getModelByName(asset['modelName'])
            parentAsset = self.getAssetByName(asset['parentName'])
            parentModel = self.getModelByName(parentAsset['modelName'])

            hierMap = {}
            for hierRef in parentModel['assetModelHierarchies']:
                hierMap[hierRef['name']] = hierRef

            self.sitewiseUtils.sitewise.associate_assets(
                assetId=parentAsset['assetId'],
                childAssetId=asset['assetId'],
                hierarchyId=hierMap[myModel['assetModelName']]['id'],
            )

            asset['change'] = 'NO'
            self.assetTable.put_item(Item=asset)

    def publishCompletion(self):
        """
        Publish a completion message to all the self.completionTopics.
        :return:
        """
        payload = {
            'AssetModelConverter': {
                'CompletionTime': datetime.utcnow().isoformat(),
            }
        }

        for topic in self.completionTopics:
            log.info(f'Publishing completion {topic}')
            self.iotData.publish(
                topic=topic,
                qos=1,
                payload=json.dumps(payload, indent=4, sort_keys=True)
            )

    def processEvent(self, event):
        self.modelList = self.createModels()
        self.assetList = self.createAssets()

        self.updateAssetModelHierarchies()
        self.updateModels()
        self.associateAssets()

        if self.modelList or self.assetList:
            self.publishCompletion()

def handler(event, context):
    CreateSitewiseResources().processEvent(event)


if __name__ == '__main__':
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s - %(message)s')
    consoleHandler.setFormatter(formatter)
    log.addHandler(consoleHandler)

    customEvent = {}
    CreateSitewiseResources().processEvent(customEvent)