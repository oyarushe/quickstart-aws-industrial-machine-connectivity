#!/usr/bin/env python3
import json
import logging
import pprint
import sys
import time

import boto3
from botocore.exceptions import ClientError

from sitewiseUtils import SitewiseUtils

log = logging.getLogger('assetModelConverter')
log.setLevel(logging.DEBUG)


if __name__ == '__main__':
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s - %(message)s')
    consoleHandler.setFormatter(formatter)
    log.addHandler(consoleHandler)

    myClass = SitewiseUtils()

    myClass.deleteAllModels()
