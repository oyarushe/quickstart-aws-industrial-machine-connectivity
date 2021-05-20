import argparse
import base64
import json
import logging
from pprint import pprint
import time
import boto3
from botocore.exceptions import ClientError
import json
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class Secret():
    def __init__(self, user_id, password, org_id, cluster):
        self.user_id = user_id
        self.password = password
        self.org_id = org_id
        self.cluster = cluster


class SecretsManager:
    def __init__(self, region_name, name):
        self.name = name
        session = boto3.session.Session()
        self._client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )

    def get_value(self):
        if self.name is None:
            raise ValueError

        try:
            kwargs = {'SecretId': self.name}
            response = self._client.get_secret_value(**kwargs)
            logger.info("Got value for secret %s.", self.name)
        except ClientError:
            logger.exception("Couldn't get value for secret %s.", self.name)
            raise

        try:
            secret = json.loads(response['SecretString'])
            user_id = secret['user_id']
            password =  secret['password']
            org_id = secret['org_id']
            cluster = secret['cluster']
        except Exception:
            logger.exception("Secret does not have correct setting")
            raise
        
        return Secret(user_id, password, org_id, cluster)
    
    def get_random_password(self, pw_length):
        try:
            response = self._client.get_random_password(
                PasswordLength=pw_length)
            password = response['RandomPassword']
            logger.info("Got random password.")
        except ClientError:
            logger.exception("Couldn't get random password.")
            raise
        else:
            return password

    def put_value(self, secret_value):
        if self.name is None:
            raise ValueError

        try:
            kwargs = {'SecretId': self.name}
            if isinstance(secret_value, str):
                kwargs['SecretString'] = secret_value
            elif isinstance(secret_value, bytes):
                kwargs['SecretBinary'] = secret_value
            response = self._client.put_secret_value(**kwargs)
            logger.info("Value put in secret %s.", self.name)
        except ClientError:
            logger.exception("Couldn't put value in secret %s.", self.name)
            raise
        else:
            return response
