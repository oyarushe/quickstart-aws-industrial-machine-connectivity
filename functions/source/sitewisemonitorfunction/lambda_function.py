import json
import boto3
import json
import uuid
import time
import argparse
import os

def createSitewiseMonitorDashboard(boto3Session, sitewiseMonitorRole):
    client = boto3Session.client('iotsitewise')
    supportEmail= os.environ.get('supportEmail')
    portalName = os.environ['stackName']

    sitewiseMonitorAssets = []

    def processAssets(assetID, hierarchyID):
        response = client.list_associated_assets(
            assetId=assetID,
            hierarchyId=hierarchyID,
        )
        #print("*******")
        #print(response)
        for asset in response['assetSummaries']:
            assetID = asset['id']
            assetHierarchies = asset['hierarchies']
            response = client.describe_asset(
                assetId=assetID
            )
            for propertyItem in response['assetProperties']:
                #print(propertyItem)
                if 'notification' in propertyItem:
                    if propertyItem['notification']['state'] == 'ENABLED':
                        if len(sitewiseMonitorAssets) < 10:
                            sitewiseMonitorAssets.append(propertyItem)
                
            for item in assetHierarchies:
                processAssets(assetID, item['id'])


    response = client.list_assets(
        filter='TOP_LEVEL'
    )
    #print(response)
    rootAsset = []
    for asset in response['assetSummaries']:
        assetID = asset['id']
        rootAsset.append(assetID)
        assetHierarchies = asset['hierarchies']
        for item in assetHierarchies:
            processAssets(assetID, item['id'])

    #print(sitewiseMonitorAssets)

    dashboardDesign = {
        'widgets':[]
    }
    y = 0
    x = 0
    for monitorAsset in sitewiseMonitorAssets:
        print(monitorAsset)
        print(" ")
        topic = monitorAsset['notification']['topic']
        assetID = topic.split('/')[5]
        propertyID = topic.split('/')[7]
        name = monitorAsset['name']
        addAWidget = {
            'type': 'monitor-line-chart',
            'title': name,
            "x": x,
            "y": y,
            "height": 3,
            "width": 3,
            "metrics": [
                {
                    "label": name,
                    "type": "iotsitewise",
                    "assetId": assetID,
                    "propertyId": propertyID
                }
            ]        
        }
        y = y + 3
        dashboardDesign['widgets'].append(addAWidget)

    print(dashboardDesign)

    # Going to create Portal

    response = client.create_portal(
        portalName=portalName,
        portalContactEmail=supportEmail,
        roleArn=sitewiseMonitorRole
    )

    print(response)

    portalID = response['portalId']
    protalCreationInProgress = True

    while protalCreationInProgress:
        print("going to sleep")
        time.sleep(5)
        response = client.describe_portal(
            portalId=portalID
        )    
        if response['portalStatus']['state'] == 'ACTIVE':
            protalCreationInProgress = False

    imcUUID = str(uuid.uuid4())

    response = client.create_project(
        portalId=portalID,
        projectName='imcproject',
    )

    print(response)
    projectID = response['projectId']

    response = client.batch_associate_project_assets(
        projectId=projectID,
        assetIds=[
            rootAsset[0]
        ]
    )

    print(response)

    response = client.create_dashboard(
        projectId=projectID,
        dashboardName='imcdashboard',
        dashboardDefinition=json.dumps(dashboardDesign),
    )
    print(response)    

def lambda_handler(event, context):
    boto3Session = boto3
    sitewiseMonitorRole = os.environ['imcmonitorrole']
    createSitewiseMonitorDashboard(boto3Session, sitewiseMonitorRole)
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
    