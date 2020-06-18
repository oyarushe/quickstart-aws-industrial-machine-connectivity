from chalice import Chalice
import boto3
from botocore.exceptions import ClientError
import time
import json

app = Chalice(app_name='ggdeployer')
gg = boto3.client('greengrass')

@app.route('/')
def index():
    return {'hello': 'world'}

@app.route('/deployggwithsitewise/{groupname}', methods=['GET'])
def deployggwithsitewise(groupname):
    print("Group Name ="+groupname)
    myPaginator = gg.get_paginator('list_groups')
    myPages = myPaginator.paginate()
    myGroup = None
    for page in myPages:
        for group in page['Groups']:
            # We only want the device 'folders'
            if group['Name'] == groupname:
                myGroup=group    
    try:
        groupId = myGroup['Id']
        groupVersionId = myGroup['LatestVersion']
        group_arn = myGroup['Arn']
        print('Creating deployment for group {}[{}] version {}'.format(
            groupname,
            groupId,
            groupVersionId,
        ))
        response = gg.create_deployment(GroupId=groupId, GroupVersionId=groupVersionId, DeploymentType='NewDeployment')
        time.sleep(15)
        # Getting group cert authority
        responseGGAuthorityList = gg.list_group_certificate_authorities(
            GroupId=groupId
        )
        print(responseGGAuthorityList)
        certAuthorityId = responseGGAuthorityList['GroupCertificateAuthorities'][0]['GroupCertificateAuthorityId']
        
        response = gg.get_group_certificate_authority(
            CertificateAuthorityId=certAuthorityId,
            GroupId=groupId
        )

        # Going to create a gateway
        pem_encoded_certificate = response['PemEncodedCertificate']
        gateway_capability_json = {
          "sources": [
            {
              "name": "Automated Gateway Config",
              "endpoint": {
                "certificateTrust": {
                  "type": "TrustAny"
                },
                "endpointUri": "opc.tcp://203.0.113.1:49320",
                "securityPolicy": "BASIC128_RSA15",
                "messageSecurityMode": "SIGN_AND_ENCRYPT",
                "identityProvider": {
                  "type": "Anonymous"
                },
                "nodeFilterRules": [
                  {
                    "action": "INCLUDE",
                    "definition": {
                      "type": "OpcUaRootPath",
                      "rootPath": "/**"
                    }
                  }
                ]
              },
              "measurementDataStreamPrefix": ""
            }
          ]
        }
        ignition_ip = None
        endpoint_uri = None
        try:
            ignition_ip = app.current_request.query_params.get('ignition-ip')
        except:
            print("Could not get ignition IP - returning just the cert")
            return pem_encoded_certificate
        if ignition_ip is None:
            print("Still None")
            return pem_encoded_certificate
        else:
            print("Got something")
            endpoint_uri = 'opc.tcp://'+ignition_ip+':62541'
        print(endpoint_uri)
        gateway_capability_json['sources'][0]['endpoint']['endpointUri'] = endpoint_uri

        try:
            sitewise_client = boto3.client('iotsitewise')
            print("printing group arn")
            print(group_arn)
            response = sitewise_client.create_gateway(
                gatewayName=groupname+'_Automated_Gateway',
                gatewayPlatform={
                    'greengrass': {
                        'groupArn': group_arn
                    }
                }
            )
            print("Going to print - gateway additon json")
            print(response)
            gateway_id = response['gatewayId']
        except Exception as e:
            print(e)
            print("Failed to do gateway creation")
            return pem_encoded_certificate
        try:
            time.sleep(5)
            response = sitewise_client.update_gateway_capability_configuration(
                gatewayId=gateway_id,
                capabilityNamespace='iotsitewise:opcuacollector:1',
                capabilityConfiguration=json.dumps(gateway_capability_json)
            )
            print("Going to print - capability json")
            print(response)

        except Exception as e:
            print(e)
            print("Failed to do gateway configuration")

        return pem_encoded_certificate
    except ClientError as cErr:
        print(cErr)
        return "Error"


@app.route('/deploygg/{groupname}', methods=['GET'])
def deploygg(groupname):
    print("Group Name =" + groupname)
    myPaginator = gg.get_paginator('list_groups')
    myPages = myPaginator.paginate()
    myGroup = None
    for page in myPages:
        for group in page['Groups']:
            # We only want the device 'folders'
            if group['Name'] == groupname:
                myGroup = group
    try:
        groupId = myGroup['Id']
        groupVersionId = myGroup['LatestVersion']
        group_arn = myGroup['Arn']
        print('Creating deployment for group {}[{}] version {}'.format(
            groupname,
            groupId,
            groupVersionId,
        ))
        response = gg.create_deployment(GroupId=groupId, GroupVersionId=groupVersionId, DeploymentType='NewDeployment')
        time.sleep(15)
        # Getting group cert authority
        responseGGAuthorityList = gg.list_group_certificate_authorities(
            GroupId=groupId
        )
        print(responseGGAuthorityList)
        certAuthorityId = responseGGAuthorityList['GroupCertificateAuthorities'][0]['GroupCertificateAuthorityId']

        response = gg.get_group_certificate_authority(
            CertificateAuthorityId=certAuthorityId,
            GroupId=groupId
        )

        # Going to create a gateway
        pem_encoded_certificate = response['PemEncodedCertificate']
        return pem_encoded_certificate
    except ClientError as cErr:
        print(cErr)
        return "Error"


@app.route('/updateconnectivity/{group_name}/withip/{core_ip}', methods=['GET'])
def updateconnectivity(group_name, core_ip):
    print("Group Name =" + group_name)
    print("Core IP = "+core_ip)
    response = gg.update_connectivity_info(
        ConnectivityInfo=[
            {
                'HostAddress': core_ip,
                'Id': core_ip,
                'PortNumber': 8883
            },
        ],
        ThingName=group_name+'Core'
    )
    print(response)
    return response
