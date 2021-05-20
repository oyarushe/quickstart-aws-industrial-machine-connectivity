""" Element Unify SiteWise Agent imports existing AWS IoT SiteWise
asset models and asset hierarchies into Element Unify
Written by Element Analytics, Inc., 2021 """

from datetime import datetime
import os
import sys
import logging
from unify_common.secrets_manager import SecretsManager
from unify_sitewise_agent.unify_sitewise_agent import ElementUnifySiteWiseAgent

log = logging.getLogger('unifySiteWiseAgent')
log.setLevel(logging.INFO)

class ElementUnifySiteWiseLambda:
    """Imports existing AWS IoT SiteWise asset models and asset hierarchies into Element Unify
    It connects to the data model in SiteWise, uploads the asset model as asset templates,
    and uploads the asset hierarchy as a dataset.
    """
    def __init__(self):
        self.secret_name = os.environ.get('secretName')
        self.region_name = os.environ.get('regionName')
        self.template_suffix = os.environ.get('templateSuffix')

    def process(self):
        """Connect to Element Unify and AWS IoT SiteWise and
        upload SiteWise asset models and assets to Element Unify
        """
        secret_manager = SecretsManager(self.region_name, self.secret_name)
        try:
            secret = secret_manager.get_value()
        except Exception as error:
            log.error('Failed to get secret %s', error)
            raise error

        agent = ElementUnifySiteWiseAgent(
            username=secret.user_id,
            password=secret.password,
            orgId=secret.org_id,
            hostname=secret.cluster,
            region_name=self.region_name,
            save_csv=False,
            upload_to_unify=True,
            template_suffix=self.template_suffix)
        agent.run()

def handler(event, context=None):
    """
    Lambda handler

    :type event: dict
    :param event: event data
    """
    log.info('Processing Event %s', event)
    sitewise_lambda = ElementUnifySiteWiseLambda()
    sitewise_lambda.process()
