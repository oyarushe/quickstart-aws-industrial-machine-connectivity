""" Element Unify SiteWise Model Sync Lambda will deploy and update
models from Element Unify to AWS IoT SiteWise

Written by Element Analytics, Inc., 2021 """

from datetime import datetime
import os
import logging
from unify_common.secrets_manager import SecretsManager
from unify_sitewise_model_sync.unify_sitewise_model_sync import ElementUnifySiteWiseModelSync

log = logging.getLogger('unifySiteWiseAgent')
log.setLevel(logging.INFO)

class ElementUnifySiteWiseModelSyncLambda:
    """Deploys and updates models from Element Unify to AWS IoT SiteWise.
    It connects to the data model in Element Unify and SiteWise, computes a delta,
    and pushes Element Unify data model deltas to SiteWise. Deltas from SiteWise are
    reported to the user as a dataset.
    """
    def __init__(self):
        self.secret_name = os.environ.get('secretName')
        self.region_name = os.environ.get('regionName')
        self.bucket_name = os.environ.get('modelSyncBucketName')

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

        model_sync = ElementUnifySiteWiseModelSync(
            username=secret.user_id,
            password=secret.password,
            orgId=secret.org_id,
            hostname=secret.cluster,
            region_name=self.region_name,
            bucket_name=self.bucket_name)
        model_sync.run()

def handler(event, context=None):
    """
    Lambda handler

    :type event: dict
    :param event: event data
    """
    log.info('Processing Event %s', event)
    model_sync_lambda = ElementUnifySiteWiseModelSyncLambda()
    model_sync_lambda.process()
