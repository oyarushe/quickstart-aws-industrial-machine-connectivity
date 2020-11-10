"""
Sitewise utilities, all of our interactions with IoTSitewise.

Written by Nathan Slawson, 2020
"""
from datetime import datetime, date
import json
import logging
import pprint
import time
import os

import boto3
from botocore.exceptions import ClientError

log = logging.getLogger('assetModelConverter')
log.setLevel(logging.DEBUG)


class SitewiseUtils:
    """
    This encapsulates our interactions with sitewise. Asset/Model creation, updating, and deletion.
    Sitewise Gateway re-deployment.
    """
    def __init__(self):
        self.sitewise = boto3.client('iotsitewise')

        self.unsupportedDataTypes = ['Template']

        self.pollWaitTime = 0.5

        self.greengrassGroupID = os.environ.get('greengrassGroupID')
        self.gatewayName = os.environ.get('gatewayName')

        if self.gatewayName:
            self.gatewayName = self.gatewayName + '_Automated_Gateway'

    @staticmethod
    def jsonSerial(obj):
        """
        This is used when converting dictionary data to JSON and vice versa. Used to support types that are not
        supported in the JSON format.
        :param obj:
        :return:
        """
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

    def createAssetModel(self, modelName, modelProperties=None, modelHierarchies=None):
        """
        Creates an asset model in sitewise
        :param modelName:
        :param modelProperties:
        :param modelHierarchies:
        :return:
        """
        log.info('Creating model {}'.format(modelName))

        if not modelProperties:
            modelProperties = []

        if not modelHierarchies:
            modelHierarchies = []

        model = self.sitewise.create_asset_model(
            assetModelName=modelName,
            assetModelProperties=modelProperties,
            assetModelHierarchies=modelHierarchies,
        )

        return self.waitForActiveAssetModel(assetModelId=model['assetModelId'])

    def listAssetModels(self):
        """
        Lists all sitewise asset models with pagination
        :return:
        """
        paginator = self.sitewise.get_paginator('list_asset_models')
        pageIterator = paginator.paginate()

        modelList = []

        for page in pageIterator:
            for assetModel in page['assetModelSummaries']:
                modelList.append(assetModel)

        return modelList

    def describeAssetModel(self, assetModelId):
        """
        Describes a specific asset model
        :param assetModelId:
        :return:
        """
        try:
            return self.sitewise.describe_asset_model(assetModelId=assetModelId)

        except self.sitewise.exceptions.ResourceNotFoundException:
            return None

    def updateAssetModel(self, assetModelId, assetModelName, hierarchies):
        """
        Updates a given asset model id with new hierarchy data
        :param assetModelId:
        :param hierarchies:
        :param overwriteData:
        :return:
        """
        log.info(f'Updating AssetModelId {assetModelName} {assetModelId}')

        response = self.sitewise.update_asset_model(
            assetModelName=assetModelName,
            assetModelId=assetModelId,
            assetModelHierarchies=hierarchies,
        )

        modelDescription = self.waitForActiveAssetModel(assetModelId=assetModelId)

        return modelDescription

    def deleteAssetModel(self, assetModelId):
        """
        Deletes an asset model id
        :param assetModelId:
        :return:
        """
        log.info(f'Deleting AssetModelId {assetModelId}')
        self.sitewise.delete_asset_model(assetModelId=assetModelId)
        modelDescription = self.describeAssetModel(assetModelId=assetModelId)
        while modelDescription and modelDescription['assetModelStatus']['state'] == 'DELETING':
            time.sleep(1)
            modelDescription = self.describeAssetModel(assetModelId=assetModelId)

    def createAsset(self, assetName, assetModelId):
        """
        Creates an asset
        :param assetName:
        :param assetModelId:
        :return:
        """
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
        """
        Updates an asset's properties with the relevant property aliases, and also turns on notification state.
        :param assetId:
        :param assetProperties:
        :param assetAliases:
        :return:
        """
        for propRef in assetProperties:
            self.sitewise.update_asset_property(
                assetId=assetId,
                propertyId=propRef['id'],
                propertyNotificationState='ENABLED',
                propertyAlias=assetAliases[propRef['name']]
            )

    def listAssets(self, assetModelId):
        """
        Lists all assets
        :param assetModelId:
        :return:
        """
        paginator = self.sitewise.get_paginator('list_assets')
        pageIterator = paginator.paginate(assetModelId=assetModelId)

        assetList = []

        for page in pageIterator:
            for asset in page['assetSummaries']:
                assetList.append(asset)

        return assetList

    def listAssociatedAssets(self, assetId, hierarchyId):
        """
        Lists all associated assets
        :param assetId:
        :param hierarchyId:
        :return:
        """
        paginator = self.sitewise.get_paginator('list_associated_assets')
        pageIterator = paginator.paginate(assetId=assetId, hierarchyId=hierarchyId)

        assocAssetsList = []

        for page in pageIterator:
            # print(json.dumps(page, indent=4, sort_keys=True, default=self.jsonSerial))
            for asset in page['assetSummaries']:
                assocAssetsList.append(asset)

        return assocAssetsList

    def describeAsset(self, assetId):
        """
        Describes a specific asset
        :param assetId:
        :return:
        """
        try:
            return self.sitewise.describe_asset(assetId=assetId)

        except self.sitewise.exceptions.ResourceNotFoundException:
            return None

    def deleteAsset(self, assetId):
        """
        Deletes an asset.
        :param assetId:
        :return:
        """
        log.info(f'Deleting AssetId {assetId}')
        self.sitewise.delete_asset(assetId=assetId)
        assetDescription = self.describeAsset(assetId=assetId)
        while assetDescription and assetDescription['assetStatus']['state'] == 'DELETING':
            time.sleep(1)
            assetDescription = self.describeAsset(assetId=assetId)

    def disassociateAllAssets(self):
        """
        Disassociates all assets. This is important when removing all of our assets, as this must be done before
        they can be removed.
        :return:
        """
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
        """
        Deletes all assets after disassociating them.
        :return:
        """
        self.disassociateAllAssets()

        assetModelsList = self.listAssetModels()
        for model in assetModelsList:
            assetsList = self.listAssets(model['id'])
            for asset in assetsList:
                self.deleteAsset(asset['id'])

    def deleteAllModels(self):
        """
        Deletes all modes. First however it must delete all the assets associated with those models.
        Then it must updatee all the models to have no hierarchy entries. After these two things are completed, the
        models can then be removed.
        :return:
        """
        self.deleteAllAssets()

        assetModelsList = self.listAssetModels()
        for model in assetModelsList:
            self.updateAssetModel(assetModelId=model['id'], assetModelName=model['name'], hierarchies=[])
        for model in assetModelsList:
            self.deleteAssetModel(model['id'])

    def getGatewayIDByName(self): 
        """
        Returns the gatewayID of a SiteWise Gateway given its name.
        :return:
        """
        gateways = self.sitewise.list_gateways()

        if 'gatewaySummaries' in gateways:
            payload = gateways['gatewaySummaries']
            while 'NextToken' in gateways:
                gateways = self.sitewise.list_gateways(NextToken = gateways['NextToken'])
                payload.extend(gateways['gatewaySummaries'])

        for gateway in payload:
            if gateway['gatewayName'] == self.gatewayName:
                print('Gateway found: {}'.format(gateway))
                print('Gateway ID: {}'.format(gateway['gatewayId']))
                return gateway['gatewayId']

        return None

    def checkGatewayMatch(self, gatewayID, greengrassGroupID):
        """
        Determines whether or not the provided gatewayID 
        is associated with the provided greengrassGroupID
        """

        gatewayDescription = self.sitewise.describe_gateway(
            gatewayId=gatewayID
        )
        gatewayGroupID = gatewayDescription['gatewayPlatform']['greengrass']['groupArn'].split('/')[-1]

        if greengrassGroupID == gatewayGroupID:
            return True
        else:
            return False
    
    def listServersByGateway(self):
        """
        Lists the data sources for a given Sitewise Gateway
        :return:
        """
        gatewayID = self.getGatewayIDByName()

        if not gatewayID:
            raise GroupDoesNotExist('Gateway with ID {} does not exist'.format(self.gatewayName))

        return self.sitewise.describe_gateway_capability_configuration(
            gatewayId=gatewayID,
            capabilityNamespace='iotsitewise:opcuacollector:1'
        )
    
    def updateGateway(self, gatewayID):
        """
        Updates a given sitewise Gateway with the
        identical gateway capability configuration
        """

        gatewayCapabilityConfiguration = self.sitewise.describe_gateway_capability_configuration(
            gatewayId=gatewayID,
            capabilityNamespace='iotsitewise:opcuacollector:1'
        )

        configuration = json.loads(gatewayCapabilityConfiguration['capabilityConfiguration'])['sources'][0]
        payload = {"sources": [configuration]}

        self.sitewise.update_gateway_capability_configuration(
            gatewayId=gatewayID,
            capabilityNamespace='iotsitewise:opcuacollector:1',
            capabilityConfiguration=json.dumps(payload)
        )