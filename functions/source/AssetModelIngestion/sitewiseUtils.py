"""
Sitewise utilities, all of our interactions with IoTSitewise.

Written by Nathan Slawson, 2020
"""
from datetime import datetime, date
import json
import logging
import pprint
import time

import boto3
from botocore.exceptions import ClientError

log = logging.getLogger('assetModelConverter')
log.setLevel(logging.DEBUG)


class SitewiseUtils:
    """

    """
    def __init__(self):
        self.sitewise = boto3.client('iotsitewise')

        self.unsupportedDataTypes = ['Template']

        self.dataTypeTable = {
            "Int8": "INTEGER",
            "Int16": "INTEGER",
            "Int32": "INTEGER",
            "Int64": "INTEGER",
            "Float": "DOUBLE",
            "Double": "DOUBLE",
            "Boolean": "BOOLEAN",
            "String": "STRING",
            "DateTime": "INTEGER"
        }

        self.pollWaitTime = 0.5

    @staticmethod
    def jsonSerial(obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError("Type %s not serializable" % type(obj))

    def waitForActiveAssetModel(self, assetModelId):
        modelDescription = self.sitewise.describe_asset_model(
            assetModelId=assetModelId
        )
        while modelDescription['assetModelStatus']['state'] != 'ACTIVE':
            time.sleep(self.pollWaitTime)
            modelDescription = self.sitewise.describe_asset_model(
                assetModelId=assetModelId
            )

        return modelDescription

    def createAssetModel(self, modelName, modelMetrics=None, modelHierarchies=None):
        log.info('Creating model {}'.format(modelName))

        modelProperties = []
        if not modelHierarchies:
            modelHierarchies = []

        if modelMetrics:
            for metric in modelMetrics:
                if metric['dataType'] in self.unsupportedDataTypes:
                    continue

                modelProperties.append({
                    'name': metric['name'],
                    'dataType': self.dataTypeTable.get(metric['dataType']),
                    'type': {
                        'measurement': {}
                    }
                })

        model = self.sitewise.create_asset_model(
            assetModelName=modelName,
            assetModelProperties=modelProperties,
            assetModelHierarchies=modelHierarchies,
        )

        return self.waitForActiveAssetModel(assetModelId=model['assetModelId'])

    def listAssetModels(self):
        paginator = self.sitewise.get_paginator('list_asset_models')
        pageIterator = paginator.paginate()

        modelList = []

        for page in pageIterator:
            for assetModel in page['assetModelSummaries']:
                modelList.append(assetModel)

        return modelList

    def describeAssetModel(self, assetModelId):
        try:
            return self.sitewise.describe_asset_model(assetModelId=assetModelId)

        except self.sitewise.exceptions.ResourceNotFoundException:
            return None

    def updateAssetModel(self, assetModelId, hierarchies=None, overwriteData=False):
        log.info(f'Updating AssetModelId {assetModelId}')
        myModelData = self.describeAssetModel(assetModelId=assetModelId)

        myHierarchies = myModelData['assetModelHierarchies']

        if hierarchies is not None:
            if overwriteData:
                myHierarchies = hierarchies
            else:
                myHierarchies += hierarchies

        response = self.sitewise.update_asset_model(
            assetModelName=myModelData['assetModelName'],
            assetModelId=assetModelId,
            assetModelHierarchies=myHierarchies,
        )

        modelDescription = self.waitForActiveAssetModel(assetModelId=assetModelId)

        return modelDescription

    def deleteAssetModel(self, assetModelId):
        log.info(f'Deleting AssetModelId {assetModelId}')
        self.sitewise.delete_asset_model(assetModelId=assetModelId)
        modelDescription = self.describeAssetModel(assetModelId=assetModelId)
        while modelDescription and modelDescription['assetModelStatus']['state'] == 'DELETING':
            time.sleep(1)
            modelDescription = self.describeAssetModel(assetModelId=assetModelId)

    def createAsset(self, assetName, assetModelId):
        log.info(f"Creating asset {assetName}")
        asset = self.sitewise.create_asset(
            assetName=assetName,
            assetModelId=assetModelId
        )

        assetDescription = self.sitewise.describe_asset(
            assetId=asset['assetId']
        )
        while assetDescription['assetStatus']['state'] != 'ACTIVE':
            # log.info('Wait 1 second until asset is active')
            time.sleep(1)
            assetDescription = self.sitewise.describe_asset(
                assetId=asset['assetId']
            )

        return assetDescription

    def updateAssetProperties(self, assetId, assetProperties, assetAliases):
        for propRef in assetProperties:
            self.sitewise.update_asset_property(
                assetId=assetId,
                propertyId=propRef['id'],
                propertyNotificationState='ENABLED',
                propertyAlias=assetAliases[propRef['name']]
            )

    def listAssets(self, assetModelId):
        paginator = self.sitewise.get_paginator('list_assets')
        pageIterator = paginator.paginate(assetModelId=assetModelId)

        assetList = []

        for page in pageIterator:
            for asset in page['assetSummaries']:
                assetList.append(asset)

        return assetList

    def listAssociatedAssets(self, assetId, hierarchyId):
        paginator = self.sitewise.get_paginator('list_associated_assets')
        pageIterator = paginator.paginate(assetId=assetId, hierarchyId=hierarchyId)

        assocAssetsList = []

        for page in pageIterator:
            # print(json.dumps(page, indent=4, sort_keys=True, default=self.jsonSerial))
            for asset in page['assetSummaries']:
                assocAssetsList.append(asset)

        return assocAssetsList

    def describeAsset(self, assetId):
        try:
            return self.sitewise.describe_asset(assetId=assetId)

        except self.sitewise.exceptions.ResourceNotFoundException:
            return None

    def deleteAsset(self, assetId):
        log.info(f'Deleting AssetId {assetId}')
        self.sitewise.delete_asset(assetId=assetId)
        assetDescription = self.describeAsset(assetId=assetId)
        while assetDescription and assetDescription['assetStatus']['state'] == 'DELETING':
            time.sleep(1)
            assetDescription = self.describeAsset(assetId=assetId)

    def disassociateAllAssets(self):
        assetModelsList = self.listAssetModels()
        for model in assetModelsList:
            assetsList = self.listAssets(model['id'])
            for asset in assetsList:
                for hierRef in asset['hierarchies']:
                    assocAssetsList = self.listAssociatedAssets(asset['id'], hierRef['id'])

                    for assocRef in assocAssetsList:
                        self.sitewise.disassociate_assets(
                            assetId=asset['id'],
                            hierarchyId=hierRef['id'],
                            childAssetId=assocRef['id'],
                        )

    def deleteAllAssets(self):
        self.disassociateAllAssets()

        assetModelsList = self.listAssetModels()
        for model in assetModelsList:
            assetsList = self.listAssets(model['id'])
            for asset in assetsList:
                self.deleteAsset(asset['id'])

    def deleteAllModels(self):
        self.deleteAllAssets()

        assetModelsList = self.listAssetModels()
        for model in assetModelsList:
            self.updateAssetModel(assetModelId=model['id'], hierarchies=[], overwriteData=True)
        for model in assetModelsList:
            self.deleteAssetModel(model['id'])
