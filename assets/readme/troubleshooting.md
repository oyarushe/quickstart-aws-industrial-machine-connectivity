### Troubleshooting

**Issue 1: Quarantined certificate in Ignition (or Kepware) doesn't show up, or data doesn’t show up for Option 1 deployments.**

First, verify that the Ignition trial period (2 hours) has not expired. If that action does not remediate the issue, repeat the process of refreshing the SiteWise Gateway:

1. Navigate to the AWS IoT SiteWise console and select Ingest -> Gateways 
2. Select the gateway created during the stack launch:
    
    Naming convention: `[name_of_stack]_Automated_Gateway`
3. Click “Edit” in the Source Configuration for Automated Gateway Config section
4. Click “Save” at the bottom. No changes are necessary. This action simply activates the SiteWise gateway to ensure data flows from the OPC UA server. 
5. If it hasn’t already been done, look for and accept the quarantined certificate in Ignition.

**Issue 2: Models and assets weren’t created in SiteWise**

Check the Lambda function responsible for creating the models and assets in SiteWise for errors:

1. In the AWS lambda console, navigate to the function named:

    `[name_of_stack]-AssetModelIngestionLambdaResource-[hash]`

2. Hit the “Monitoring” tab
3. Click “View logs in CloudWatch”
4. Click into the most recent Log Stream and find the error message

**Issue 3: Models and assets weren’t created in SiteWise**

Check the Lambda function responsible for creating the models and assets in SiteWise for errors:

1. In the AWS lambda console, navigate to the function named 
 
    `[name_of_stack]-AssetModelIngestionLambdaResource-[hash]`

2. Hit the “Monitoring” tab
3. Click “View logs in CloudWatch”
4. Click into the most recent Log Stream and find the error message

**Issue 4: Data via the MQTT Transmission module doesn’t show up in IoT Cloud**

1. Get the public IP address of that instance, and load a URL like this into your browser of choice:

    `http://[hardwarePrivateIP]:8088`

2. Open the Ignition Web UI is open, you should see a gear like icon on the left labeled ‘Config’. Click that, and it will ask you to log in. The default credentials are: 
    1. Username: admin
    2. Password: password
    3. If you haven’t already, it is recommended that you change your password once you’ve successfully logged into the Ignition web UI.
3. Navigate to “MQTT Transmission -> Settings -> Server” and confirm that the connectivity shows 1 of 1. If it doesn’t, click edit and:
    1. Make sure the URL is in the format: `ssl://[your_aws_account_iot_endpoint]:8883`
    2. Download the .tar.gz file that represents the non-GreenGrass IoT thing from the following S3 bucket location:
        * Bucket Name: `[stack_name]-devicesbucketresource-hash`
        * Key Name: `[name_for_edge_device_parameter]/[name_for_edge_device_parameter]Device.tar.gz`
    3. Expand the tarball
    4. Replace the CA Certificate File with “root.ca.pem” from the tarball package
    5. Replace the Client Certificate File with the “.pem” file from the tarball package
    6. Replace the Client Private Key File with the “.private” file from the tarball package
    7. Hit “Save Changes”, and make sure that the connectivity says “1 of 1”.
