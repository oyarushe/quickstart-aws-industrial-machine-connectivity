import os
import json
import logging
import threading
import pprint
import boto3
import cfnresponse
import time
import sys

from botocore.exceptions import ClientError

from cleanupQuicksight import CleanupQuicksight
from sitewiseUtils import SitewiseUtils

s3 = boto3.resource("s3")
greengrass = boto3.client("greengrass")
sitewise = boto3.client("iotsitewise")

stackName = os.environ['stackName']
region = os.environ['AWS_REGION']

def lambda_handler(event, context):
    # make sure we send a failure to CloudFormation if the function
    # is going to timeout
    timer = threading.Timer((context.get_remaining_time_in_millis()
              / 1000.00) - 0.5, timeout, args=[event, context])
    timer.start()

    print('Received event: %s' % json.dumps(event))
    status = cfnresponse.SUCCESS

    try:
        if event['RequestType'] == 'Delete':
            delete_greengrass = event['ResourceProperties']['delete_greengrass']
            if (delete_greengrass == 'Yes'):
                group_names = event['ResourceProperties']['group_names']
                for group_name in group_names:
                    reset_greengrass_deployment(group_name)
            buckets = event['ResourceProperties']['buckets']
            clear_s3_buckets(buckets)
            delete_sitewise_portal()
            CleanupQuicksight(region=region, stackName=stackName).cleanup()
            delete_models = event['ResourceProperties']['delete_models']
            if (delete_models == 'Yes'):
                sitewiseUtils = SitewiseUtils()
                sitewiseUtils.deleteAllModels()
    except Exception as e:
        logging.error('Exception: %s' % e, exc_info=True)
        status = cfnresponse.FAILED

    finally:
        timer.cancel()
        cfnresponse.send(event, context, status, {}, None)

def delete_sitewise_portal():
  portalsList = sitewise.list_portals()
  try: 
    for portal in portalsList['portalSummaries']:
      print(portal)
      if stackName in portal['name']:
        projectList = sitewise.list_projects(
          portalId=portal['id'],
        )
        for project in projectList['projectSummaries']:
          dashboardList = sitewise.list_dashboards(
            projectId = project['id']
          )
          for dashboard in dashboardList['dashboardSummaries']:
            deleteDashboard = sitewise.delete_dashboard(
              dashboardId = dashboard['id']
            )
            time.sleep(2)
          deleteProject = sitewise.delete_project(
            projectId = project['id']
          )
          time.sleep(2)
        accessList = sitewise.list_access_policies(
          resourceType='PORTAL',
          resourceId=portal['id'],
        )
        for accessPolicy in accessList['accessPolicySummaries']:
          deleteAccessPolity = sitewise.delete_access_policy(
            accessPolicyId=accessPolicy['id'],
          )
          time.sleep(2)
        deleteProtal = sitewise.delete_portal(
          portalId = portal['id']
        )
        print(deleteProtal)
        time.sleep(2)
  except Exception as e: 
    print("Error:", e)

def clear_s3_buckets(buckets):

    for bucket in buckets:
        bucket_resource = s3.Bucket(bucket)
        bucket_resource.objects.all().delete()

def reset_greengrass_deployment(group_name):
    groups = greengrass.list_groups()
    if 'Groups' in groups:
        payload = groups['Groups']
        while 'NextToken' in groups:
            groups = greengrass.list_groups(
                NextToken = groups['NextToken'])
            payload.extend(groups['Groups'])
    for group in payload:
        if group['Name'] == group_name:
            group_id = group['Id']
            break
    response = greengrass.reset_deployments(
        Force = True,
        GroupId = group_id)

def timeout(event, context):
    logging.error('Execution is about to time out, sending failure response to CloudFormation')
    cfnresponse.send(event, context, cfnresponse.FAILED, {}, None)