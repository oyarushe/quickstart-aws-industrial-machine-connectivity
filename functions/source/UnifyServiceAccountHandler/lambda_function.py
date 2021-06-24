"""
Create Unify machine user and save the credential in Secret Manager

Written by Element Analytics, Inc., 2021
"""

import os
import sys
# unify_scripts/deploy_to_repo.sh copy "unify_common" under the lambda zip package
# for local development, add source folder to python path to import unify_common
package_dir = os.path.dirname(os.path.abspath(__file__))
if (os.path.exists(package_dir + '/local.ini')):
    sys.path.append(os.path.dirname(package_dir))

from unify_common.secrets_manager import SecretsManager
import json
import uuid
from unify.properties import Properties, ClusterSetting
from unify.orgadmin import OrgAdmin
import logging
import cfnresponse


log = logging.getLogger('setSecret')
log.setLevel(logging.INFO)

def set_machine_user_secret(region_name, stack_name, secret_name, cluster, user_name, password, org_id):
    log.info('--------set secret %s ---------', secret_name)
 
    secretsManager = SecretsManager(region_name, secret_name)
    secretsManager.name = secret_name
    mu_id = str(uuid.uuid4())
    mu_password = secretsManager.get_random_password(32)
    mu_name = "IMC Service Account-{}".format(stack_name)
    app = 'aws'

    try:
        props = Properties(ClusterSetting.MEMORY)
        props.store_cluster(user_name, password, cluster, app)
        org = OrgAdmin(app, props)
        props.set_auth_token(
            token=org.auth_token(),
            cluster=app
        )
    except Exception as error:
        log.error('Failed to login with given user credential')
        raise error
    
    try:
        machineUser = org.invite_machine_user(org_id, mu_id, mu_password, mu_name, 'Contributor')
        log.info('Created machine user with id %s', str(machineUser['userId']))
    except Exception as error:
        log.error('Failed to create machine user')
        raise error
    
    try:
        response = secretsManager.put_value(json.dumps({
            'cluster': cluster,
            'org_id': org_id,
            'user_id': mu_id,
            'password': mu_password,
            'user_name': mu_name
        }))
    except Exception as error:
        log.error('Failed to store machine user in secret')
        raise error
    else:
        log.info('Created machine user {} in secret.'.format(mu_name))
        return response

def lambda_handler(event, context):
    log.info('EVENT: {}'.format(event))
    if event['RequestType'] == 'Create' or event['RequestType'] == 'Update':
        log.info('Set unify secret when stack get created or updated')
        try:
            resourceProps = event['ResourceProperties']
            region_name = resourceProps['Region']
            stack_name = resourceProps['StackName']
            secret_name = resourceProps['SecretName']
            cluster = resourceProps['UnifyHost']
            user_name = resourceProps['UserName']
            password = resourceProps['Password']
            org_id = resourceProps['OrgId']
            set_machine_user_secret(region_name, stack_name, secret_name, cluster, user_name, password, org_id)
        except Exception as error:
            cfnresponse.send(event, context, cfnresponse.FAILED, {})
            raise error

    responseData = {}
    cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)

# For testing setMachineSecret
if __name__ == "__main__":
    region_name = "us-east-1"
    stack_name = 'test_stack_1'
    secret_name = 'imcUnifyTest001'
    cluster = os.getenv('cluster')
    user_name = os.getenv('username')
    password = os.getenv('password')
    org_id = os.getenv('org_id')

    set_machine_user_secret(region_name, stack_name, secret_name, cluster, user_name, password, org_id)

  