import sys
import logging
import time
import os
import json
from datetime import datetime

import boto3
from botocore.exceptions import ClientError 

# Configure logging
log = logging.getLogger('SiteWiseS3Dump')
log.setLevel(logging.INFO)
streamHandler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
log.addHandler(streamHandler)

class SiteWiseS3Dump():

    def __init__(self):
        self.sitewise = boto3.client('iotsitewise')
        self.s3 = boto3.client('s3')
        self.bucket_name = os.environ.get('BucketName', 'bpxirelandtest')
    
    def __datetime_converter(self, o):
        if isinstance(o, datetime):
            return o.__str__()

    def get_all_models(self):
        """
        Gets all models in SiteWise
        :Returns:
        List of models
        """
        response = self.sitewise.list_asset_models()
        models = response['assetModelSummaries']
        while 'nextToken' in response:
            response = self.sitewise.list_asset_models(nextToken=response['nextToken'])
            models.extend(response['assetModelSummaries'])
        return models
    
    def get_all_assets(self, models):
        """
        Gets all assets in SiteWise
        :Params:
        models - list of assets produced from the get_all_models method
        :Returns:
        List of assets
        """
        all_assets = []
        for model in models:
            log.info(f"Getting assets for model: {model['id']}")
            response = self.sitewise.list_assets(assetModelId=model['id'])
            all_assets.extend(response['assetSummaries'])
            while 'nextToken' in response:
                response = self.sitewise.list_assets(nextToken=response['nextToken'])
                all_assets.extend(response['assetSummaries'])
        return all_assets

    def upload_to_s3(self, payload):
        """
        Puts an object into S3 with the payload provided
        """
        try:
            self.s3.put_object(
                Body=str(json.dumps(payload, default=self.__datetime_converter, indent=4)),
                Bucket=self.bucket_name,
                Key='sitewise_resources.json'
            )
        except ClientError as e:
            log.error(f'S3 bucket ({self.bucket_name}) does not exist: {e}')
        except Exception as e:
            log.error(f'An error occurred when trying to put SiteWise data into S3: {e}')
            
    def get_entity_count(self, entities):
        """
        Get the total count of assets or models
        :Returns:
        Asset or model count, as an integer
        """
        count = 0
        for entity in entities:
            count = count + 1
        return count 

    def generate_payload(self, models, assets):
        """
        Given a list of models and assets, generates JSON to be put in S3
        :Params:
        models - list of models
        assets - list of assets
        :Returns:
        payload - JSON to be put in S3
        """
        # date_object = datetime.utcnow()
        # print(date_object.strftime("%b-%d-%Y %H:%M:%S.%f"))
        payload = {
            'datetime': datetime.utcnow(),
            'models': {},
            'assets': {}
        }
        for model in models:
            payload['models'][model['name']] = model
        for asset in assets:
            payload['assets'][asset['name']] = asset
        return payload

    def process_event(self):
        """
        Main event handler for the class
        """
        models = self.get_all_models()
        assets = self.get_all_assets(models)
        payload = self.generate_payload(models, assets)
        self.upload_to_s3(payload)

        # model_count = self.get_entity_count(models)
        # asset_count = self.get_entity_count(assets)
        # log.info(f'Total number of models: {model_count}')
        # log.info(f'Total number of assets: {asset_count}')

def lambda_handler(context, event):
    sitewise_s3_dump = SiteWiseS3Dump()
    sitewise_s3_dump.process_event()