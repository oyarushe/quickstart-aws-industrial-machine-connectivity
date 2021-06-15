#!/usr/bin/env python3
from datetime import datetime, date
import json
import logging
import sys

import boto3

log = logging.getLogger('assetModelConverter')
log.setLevel(logging.DEBUG)


class CleanupQuicksight:
    def __init__(self, region):
        self.session = boto3.session.Session(region_name=region)
        self.accountID = boto3.client('sts').get_caller_identity()['Account']

        self.quickSight = self.session.client('quicksight')

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

    def getDataSets(self):
        nextToken = None

        dataSetList = []

        while True:
            args = {
                'AwsAccountId': self.accountID,
                'MaxResults': 100,
            }
            if nextToken:
                args['NextToken'] = nextToken

            response = self.quickSight.list_data_sets(**args)
            if response['Status'] != 200:
                raise Exception('Failure to list data sets')

            nextToken = response.get('NextToken')

            dataSetList.extend(response['DataSetSummaries'])

            if not nextToken:
                break

        return dataSetList

    def getDataSources(self):
        nextToken = None

        dataSourceList = []

        while True:
            args = {
                'AwsAccountId': self.accountID,
                'MaxResults': 100,
            }
            if nextToken:
                args['NextToken'] = nextToken

            response = self.quickSight.list_data_sources(**args)
            if response['Status'] != 200:
                raise Exception('Failure to list data sets')

            nextToken = response.get('NextToken')

            dataSourceList.extend(response['DataSources'])

            if not nextToken:
                break

        return dataSourceList

    def cleanup(self):
        myDataSets = self.getDataSets()
        for dataSet in myDataSets:
            if dataSet['Name'].startswith('imc'):
                log.info('Removing DataSet: {} {}'.format(dataSet['Name'], dataSet['DataSetId']))
                self.quickSight.delete_data_set(
                    AwsAccountId=self.accountID,
                    DataSetId=dataSet['DataSetId']
                )

        myDataSources = self.getDataSources()
        for dataSource in myDataSources:
            if dataSource['Name'].startswith('imc'):
                log.info('Removing DataSource: {} {}'.format(dataSource['Name'], dataSource['DataSourceId']))
                self.quickSight.delete_data_source(
                    AwsAccountId=self.accountID,
                    DataSourceId=dataSource['DataSourceId']
                )


if __name__ == '__main__':
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s - %(message)s')
    consoleHandler.setFormatter(formatter)
    log.addHandler(consoleHandler)

    CleanupQuicksight(region='us-east-1').cleanup()
    # CleanupQuicksight(region='us-west-2').cleanup()
