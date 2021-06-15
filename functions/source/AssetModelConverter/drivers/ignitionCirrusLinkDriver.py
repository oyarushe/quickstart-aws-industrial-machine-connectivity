#!/usr/bin/env python3
import collections.abc
from datetime import date, datetime
import json
import logging
import os
import re
import sys
import time

import boto3
from botocore.exceptions import ClientError

log = logging.getLogger('assetModelConverter')
log.setLevel(logging.DEBUG)


class CirrusLinkDriver:
    def __init__(self):
        self.boto3Session = boto3.Session()
        self.dynamo = self.boto3Session.resource('dynamodb')
        self.assetModelTable = self.dynamo.Table(os.environ['DynamoDB_Model_Table'])
        self.assetTable = self.dynamo.Table(os.environ['DynamoDB_Asset_Table'])

        self.saveAMCData = os.environ.get('SaveAMCData', False)

        # Max depth of placeholder models to create, usually set to the max depth that sitewise will allow.
        self.hierarchyMaxDepth = 10

        # This is the property alias prefix.
        # TODO In the future this may use a configurable value to uniquely identify data coming from a specific
        #      instance of ignition.
        self.tagAliasPrefix = '/Tag Providers/default'

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
        self.unsupportedDataTypes = ['Template']

        # Timestamp format to use when printing or writing messages/file/folder names
        self.timestampFormat = '%Y-%m-%d_%H-%M-%S'

        # models stores all of our model structure
        self.models = {}
        # used to store our asset structure
        self.assets = {}
        # depth model map has our mapping by depth to the place holder models
        self.depthModelMap = {}

        self.normalizedModels = {}
        self.normalizedAssets = {}

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

    def updateDict(self, baseData, updateData):
        """
        Updates the baseData dictionary with the contents of updateData.
        :param baseData:
        :param updateData:
        :return:
        """
        for key, value in updateData.items():
            if isinstance(value, collections.abc.Mapping):
                baseData[key] = self.updateDict(baseData.get(key, {}), value)
            else:
                baseData[key] = value

        return baseData

    def buildStructure(self, topicList, value):
        """
        Un-squashes a path structure from the birth message topic.
        :param topicList:
        :param value:
        :return:
        """
        if not topicList:
            return value

        pathSeg = topicList.pop(0)
        childNode = self.buildStructure(topicList, value)

        return {pathSeg: childNode}

    def processBirthObjects(self, birthData):
        for birth in birthData:
            cleanedTopic = birth['topic'].split('/')
            cleanedTopic.pop(2)
            cleanedTopic.pop(0)
            # cleanedTopicString = '/'.join(cleanedTopic)

            if 'metrics' not in birth:
                log.info('Invalid/deprecated birth message format detected, skipping: {}'.format(birth))
                continue

            for metric in birth['metrics']:
                # Skipping metrics that are for internal ignition usage
                if type(metric['value']) != dict or metric['value'].get('isDefinition') is None:
                    continue

                # metricFullName = cleanedTopicString + '/' + metric['name']
                # log.info(metricFullName)
                mVal = metric['value']
                if mVal['isDefinition']:
                    self.models[metric['name']] = mVal
                else:
                    assetPath = cleanedTopic + [metric['name']]
                    assetValue = self.buildStructure(assetPath, mVal)

                    self.updateDict(self.assets, assetValue)

    def saveData(self, data, filename):
        """
        Writes a dictionary to a file as JSON.
        :param data:
        :param filename:
        :return:
        """
        with open(filename, 'w', encoding='utf-8') as dataFile:
            dataFile.write(json.dumps(data, indent=4, sort_keys=True, default=self.jsonSerial))

    def loadData(self, filename):
        """
        Loads a JSON file into a dictionary.
        :param filename:
        :return:
        """
        with open(filename, 'r', encoding='utf-8') as dataFile:
            return json.load(dataFile)

    def genModelNode(self, name, modelMetrics, parentName='root'):
        modelNode = {
            "assetModelName": name,
            "parent": parentName,
            "assetModelProperties": [],
            "assetModelHierarchies": [],
            "change": 'YES'
        }

        for metric in modelMetrics:
            if metric['dataType'] in self.unsupportedDataTypes:
                continue

            modelNode['assetModelProperties'].append({
                'name': metric['name'],
                'dataType': self.dataTypeTable.get(metric['dataType']),
                'type': {
                    'measurement': {}
                }
            })

        return modelNode

    def generatePlaceholderModels(self, depthLevel=0, parentName='root'):
        """
        By depth level, creates placeholder models. These are used to store asset structure folders.
        :param depthLevel:
        :return:
        """
        if depthLevel >= self.hierarchyMaxDepth:
            return None

        if depthLevel == 1:
            pName = '__Node'
        elif depthLevel == 0:
            pName = '__Group'
        else:
            pName = f'__DeviceLevel{depthLevel-1}'

        modelNode = self.genModelNode(
            name=pName,
            modelMetrics=[],
            parentName=parentName,
        )

        self.normalizedModels[pName] = modelNode
        self.depthModelMap[depthLevel] = modelNode

        self.generatePlaceholderModels(depthLevel=depthLevel + 1, parentName=pName)

    def getAssetNodeType(self, nodeValue):
        """
        This is how we decide if a given node is an actual asset instance, or merely folder structure
        :param nodeValue:
        :return:
        """
        if 'isDefinition' in nodeValue and 'reference' in nodeValue:
            return 'asset'
        else:
            return 'folder'

    def getAssetNodeData(self, nodeValue, depthLevel):
        """
        Uses the nodeValue of the asset level tree and the current depth to return the nodeType and base model reference.
        :param nodeValue:
        :param depthLevel:
        :return:
        """
        nodeType = self.getAssetNodeType(nodeValue)

        if nodeType == 'asset':
            # self.genModelNode()
            referenceName = nodeValue['reference']
            derivedModelName = referenceName + f'_D{depthLevel}'

            if derivedModelName not in self.normalizedModels:
                self.normalizedModels[derivedModelName] = self.genModelNode(
                    name=derivedModelName,
                    modelMetrics=self.models[referenceName]['metrics'],
                )

            baseModelName = derivedModelName
        else:
            baseModelName = self.depthModelMap[depthLevel]['assetModelName']

        return nodeType, baseModelName

    def genAssetNode(self, nodeName, baseModel, tagsList, parentName=''):
        assetNode = {
            'assetName': nodeName,
            'modelName': baseModel,
            'change': 'YES',
            'tags': [],
        }

        if tagsList:
            assetNode['tags'] = []

            for tag in tagsList:
                tagPath = tag['properties']['ConfiguredTagPath']['value']

                tagEntry = {
                    'tagName': tag['name'],
                    'tagPath': re.sub('^\[.+\]', self.tagAliasPrefix + '/', tagPath)
                }
                assetNode['tags'].append(tagEntry)

        if parentName:
            assetNode['parentName'] = parentName

        return assetNode

    def processAssetTree(self, nodeName, nodeValue, depthLevel=0, parentPath=''):
        """
        Recursively walks self.assets, creating assets, and their associated property aliases where relevant.
        :param nodeName:
        :param nodeValue:
        :param depthLevel:
        :param parentPath:
        :return:
        """
        nodePath = parentPath + '/' + nodeName
        log.info(nodePath)
        nodeType, baseModelName = self.getAssetNodeData(nodeValue, depthLevel)

        metricsList = None
        if 'metrics' in nodeValue:
            metricsList = nodeValue['metrics']

        assetNode = self.genAssetNode(
            nodeName=nodePath,
            baseModel=baseModelName,
            tagsList=metricsList,
            parentName=parentPath,
        )
        self.normalizedAssets[nodePath] = assetNode

        # Process child nodes
        if nodeType == 'folder':
            for childName, childValue in nodeValue.items():
                self.processAssetTree(
                    nodeName=childName,
                    nodeValue=childValue,
                    depthLevel=depthLevel+1,
                    parentPath=nodePath,
                )

    def createDynamoRecords(self, table, data, primaryKey):
        for record in data:
            try:
                # log.info(record)
                table.put_item(Item=record, ConditionExpression=f'attribute_not_exists({primaryKey})')
                time.sleep(0.1)

            except ClientError as cErr:
                if cErr.response['Error']['Code'] == 'ConditionalCheckFailedException':
                    log.info('Ignoring existing record {}'.format(record[primaryKey]))
                else:
                    raise

    def processEvent(self, event):
        log.info(event)

        self.processBirthObjects(event['birthData'])

        if self.saveAMCData:
            self.saveData(self.assets, 'assetsRaw.json')
            self.saveData(self.models, 'modelsRaw.json')

        try:
            self.generatePlaceholderModels()

            for assetGroup in self.assets:
                self.processAssetTree(assetGroup, self.assets[assetGroup])

            dynamoAssets = [value for value in self.normalizedAssets.values()]
            dynamoModels = [value for value in self.normalizedModels.values()]

            if self.saveAMCData:
                self.saveData(dynamoAssets, 'assets.json')
                self.saveData(dynamoModels, 'models.json')

            self.createDynamoRecords(self.assetModelTable, dynamoModels, 'assetModelName')
            self.createDynamoRecords(self.assetTable, dynamoAssets, 'assetName')

        except ClientError as cErr:
            log.exception('Failed to process birth objects')


def handler(event, context):
    CirrusLinkDriver().processEvent(event)


if __name__ == '__main__':
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s - %(message)s')
    consoleHandler.setFormatter(formatter)
    log.addHandler(consoleHandler)

    customEvent = {}

    os.environ['OverrideScanTime'] = '1'
    os.environ['SaveAMCData'] = 'Yes'
    os.environ['IncomingBucket'] = 'nathanimcenv-amcincomingresource-11urj0786l9n1'
    CirrusLinkDriver().processEvent(customEvent)
