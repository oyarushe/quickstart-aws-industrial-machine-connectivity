## Element Unify Troubleshooting

>This document provides a reference for troubleshooting when working with Element Unify.

### Quick Start Reference Deployment

#### Issue 1: UnifyVirtual1 and UnifyVirtual2 resources fail to create.

First, navigate to the stack from `workload > resources`. Then click on events to see if there are any issues. Check CloudWatch to see if there are any issues with any of the resources associated with `UnifyVirtual1` or `UnifyVirtual2`.

One possible error is due to an existing SiteWise gateway. You will need to choose a different name for the edge-gateway device and site prefix combination.

```
An error occurred (ResourceAlreadyExistsException) when calling the CreatePolicy operation; Policy cannot be created - name already exists
```

#### Issue 2: UnifyServiceAccountHandlerTrigger has an error.

First, navigate to the stack from `workload > resources`. Then click on events to see if there are any issues. Check CloudWatch to see if there are any issues with any of the resources associated with `UnifyServiceAccountHandlerTrigger`.

A possible error is that the hostname or user credential is incorrect.
1. Navigate to the hostname using Google Chrome.
2. Check to make sure the login works. If it does not work, reset password.
3. Run the stack creation again.

#### Issue 3: Ignition data does not flow to AWS IoT SiteWise.

Check to make sure aliases are properly set.

1. In Element Unify dataset, make sure the Mapping field starts with the datastream prefix defined during stack creation. The Mapping field should follow the pattern `[datastream prefix]/Tag Provider/default/[tag name]`
2. In the AWS IoT SiteWise console, navigate to Gateways.
3. Click on the gateway associated with the Ignition device.
4. Click on the gateway device.
5. Check the datastream prefix field is set as expected. If not, click on edit and set to the expected prefix.
6. Check to make sure the device status is In Sync.

Check to make sure the Ignition server has a trusted certificate.

1. Get the public IP address of that instance, and load a URL like this into your browser of choice:
`http://[hardwarePublicIP]:8088`
2. Open the Ignition Web UI is open, you should see a gear like icon on the left labeled ‘Config’. Click that, and it will ask you to log in. The default credentials are:
A. Username: admin
B. Password: password
3. If you haven’t already, it is recommended that you change your password once you’ve successfully logged into the Ignition web UI.
4. Navigate to "OPC UA -> Security -> Server" and wait for the quarantined certificate to appear (from AWS IoT SiteWise Gateway). You should see a single entry under `Quarantined Certificates` named something like `AWS IoT SiteWise Gateway Client`.
5. Click “Trust” to accept the certificate. At this point, the SiteWise connector will start consuming data over OPC UA from Ignition and this data will be sent up to the AWS IoT SiteWise in the cloud.

One possible error is due to an existing SiteWise gateway. You will need to choose a different name for the edge-gateway device and site prefix combination.

```
An error occurred (ResourceAlreadyExistsException) when calling the CreatePolicy operation: Policy cannot be created - name already exists
```

### Training / User Guide

#### Issue 1: Changed property type in Element Unify does not publish to AWS IoT SiteWise.

Check to make sure the property type in Element Unify template attribute configuration property is valid: `Measurement`, `Attribute`, `Metric`, or `Transform`.

The SiteWise updater lambda runs once an hour. The lambda can be run manually. See steps 3 and 4.
1. In the AWS IoT SiteWise console, navigate to the asset model and property.
2. Delete the property. This is because once a property type is set in SiteWise, the type cannot be changed without first removing the property.
3. In the AWS Lambda console, navigate to the `[name of stack]-UnifySiteWiseUpdater-[hash]` resource.
4. Click on the Test tab, and manually trigger a re-publish.

#### Issue 2: Changed property data type in Element Unify does not publish to AWS IoT SiteWise.

The SiteWise updater lambda runs once an hour. The lambda can be run manually. See steps 3 and 4.
1. In the AWS IoT SiteWise console, navigate to the asset model and property.
2. Delete the property. This is because once a property data type is set in SiteWise, the data type cannot be changed without first removing the property.
3. In the AWS Lambda console, navigate to the `[name of stack]-UnifySiteWiseUpdater-[hash]` resource.
4. Click on the Test tab, and manually trigger a re-publish.

#### Issue 3: Removed assets or asset models in Element Unify are not deleted in AWS IoT SiteWise.

Assets and asset models that have been removed in Element Unify will need to be explicitly deleted in AWS IoT SiteWise per design to prevent accidental deletion. A dataset in Element Unify Dataset Catalog captures any SiteWise asset model, asset, or asset hierarchy relationship that needs to be explicitly deleted.
1. In Element Unify, navigate to the Dataset Catalog.
2. Click on the dataset called `SiteWise - Objects to Delete`. This lists each object in SiteWise that should be deleted.
3. In the AWS IoT SiteWise console, navigate to the asset model, asset, or property.
4. Delete the object.

#### Issue 4: SiteWise asset created, but not attached to correct parent asset.

Check the Lambda function responsible for publishing the Element Unify data model to AWS IoT SiteWise for errors:
1. In the AWS lambda console, navigate to the function named:
`[name_of_stack]-UnifySiteWiseUpdater-[hash]`
2. Hit the “Monitoring” tab
3. Click “View logs in CloudWatch”
4. Click into the most recent Log Stream and find the error message
5. If the function reached the maximum timeout (15 minutes), run the function again.
6. In AWS IoT SiteWise, check to make sure the asset hierarchy definition between the asset and parent asset is defined. In Element Unify, check that a similar attribute exists on the template that defines the recursive template relationship.
7. In Element Unify, check to make sure ancestor assets are defined and mapped to an asset template.
8. In Element Unify, make sure the dataset for the model sync contains the required headers: `Asset Name`, `Asset Model`, `Asset Property`, `Asset Path`, `Mapping`.

#### Issue 5: Uploaded source file to S3 not processed.

Check the Lambda function responsible for ingesting source system exports to Element Unify for errors:
1. In the AWS lambda console, navigate to the function named:
`[name_of_stack]-UnifySourceIngest-[hash]`
2. Hit the “Monitoring” tab
3. Click “View logs in CloudWatch”
4. Click into the most recent Log Stream and find the error message

>Note that for Ignition, version 8.0 is supported.

#### Issue 6: Existing AWS IoT SiteWise objects not loaded into Element Unify.

Check the Lambda function responsible for ingesting the AWS IoT SiteWise data model to Element Unify for errors:
1. In the AWS lambda console, navigate to the function named:
`[name_of_stack]-UnifySiteWiseIngest-[hash]`
2. Hit the “Monitoring” tab
3. Click “View logs in CloudWatch”
4. Click into the most recent Log Stream and find the error message
