# IMC Quickstart for AWS IoT Sitewise
something about virtual option 1

## Requirements:
- AWS account with SSO enabled: https://docs.aws.amazon.com/singlesignon/latest/userguide/getting-started.html

## Getting Started

### EC2 Key Pair
We're going to need a key pair to use for spinning up our EC2 Instances. You can use an existing key, or you can 
create a new one for this quickstart: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html

Whichever option is chosen, we just need to make sure we have the appropriate .pem file downloaded and available.

### Quickstart Bucket Preparation
Next we need an S3 bucket to store all the Cloudformation artifacts that aren't simply inline'd into the template.
Once it's created, we copy the 'quickstart' folder into the bucket. 

At this point, the contents of our Quickstart bucket should look something like this:
```
quickstart/
  functions/
  scripts/
  templates/
  LICENSE.txt
  NOTICE.txt
  README.md
```

### Cloudformation Deployment
Now we'll open up the Cloudformation console, and create a new stack using the workload template that's in our bucket.
The URL should look something like this:
https://<BUCKETNAME>.s3.amazonaws.com/templates/IMC-workload.template.yaml

#### Configure the Stack
Next we'll need to configure our stack details. Give it a stack name, and for the sake of this guide, 
configure the other options like so:

##### **Edge Deployment Configuration**

* Stack Name: Give the stack a name
**Edge Deployment Configuration**
* Edge device name: If desired, you may specify the name of the Greengrass group that gets created along with your stack under “Name for the edge device”
* Type of deployment: Select type “Virtual” 
* Deployment flow: Select deployment flow “Option1”
 
**Amazon EC2 Configuration**
* SSH Key Name: Select your SSH Key Name (EC2 Key Pair)
* VPC ID: Select your account’s default VPC 
* Greengrass/Ignition EC2 Instance Types: You may specify the size of the EC2 instances that get created as part of the solution. Suggested: leave the as the default values
* EC2 AMI: Select “ami-085925f297f89fce1” from the dropdown menu
* EC2 Subnet: Select the VPC Subnet associated with availability zone us-east-1a in your account

**AWS Quick Start Configuration**
* QuickStart S3 Bucket Name: Use the name of the bucket you created in step **"Quickstart Bucket Preparation"**
* QuickStart S3 Prefix: Use “quickstart/“ 
* QuickStart S3 Bucket Region: Leave as default “us-east-1”
* AMC Driver: Leave as default “IgnitionCirrusLink”
* User Public IP Address: Input your public IP address in the format “x.x.x.x” so that you have access to SSH into the EC2 instances

#### Deploy
Once you're done configuring, deploy the stack, and wait for completion. This will take some time.

### Post Deployment Steps

#### Verify Sitewise Asset Creation
After the deployment completes, you'll want to head over to the AWS IoT Sitewise console page. From there you can watch as
the assets and models are created in Sitewise, and associated with each other into a single hierarchy. 
This will take a while(up to 10 minutes), but once it's completed you should see an asset structure much like this one:
```
/AWS Smart Factory
  /AWS Smart Factory/Smart Factory 1
    /AWS Smart Factory/Smart Factory 1/Line 1
      /AWS Smart Factory/Smart Factory 1/Line 1/Conveyer
      /AWS Smart Factory/Smart Factory 1/Line 1/Hauloff
      /AWS Smart Factory/Smart Factory 1/Line 1/Stamping Machine
...
```

#### Accept Sitewise Certificate in Ignition
Now we need to access the web UI of the Ignition server. If you go to the AWS EC2 Console, you should see an instance
named something like:
```
Virtual/Option1/Ignition
```
Get the public IP address of that instance, and load a url like this into your browser of choice:
```
http://<IginitionServerPublicIP>:8088
```
Once loaded, you should see a gear like icon on the left labeled 'Config'. Click that, and it will ask you to log in.
The default username and password are 'admin' and 'password'.(You may wish to change this, but for now use the defaults)

Navigate to "OPC UA -> Security -> Server" and wait for the quarantined certificate to appear (from AWS IoT SiteWise).
You should see a single entry under 'Quarantined Certificates' named something like 'AWS IoT SiteWise Gateway Client'.
Go ahead and click 'Trust'.

#### Validate Incoming PLC Data
Now that you've trusted the certificate, go back to the AWS IoT Sitewise dashboard. If you click on assets, and select one
in the tree that has various measurements(Like a 'Hauloff' or a 'Conveyer' for example), you should see data start to appear
and change under 'Measurements'. This indicates that the Ignition simulation of those virtual devices and sensors is
properly sending data through to AWS IoT Sitewise.

#### View Sitewise Portal Data
For a more visual display of the data, let's head over to the 'Portals' section of the AWS Iot Sitewise page. You should
select the "name" of the Portal most recently added (the topmost on the list). Add yourself as an administrator of the Portal, click the "URL", then click on the single dashboard to view your data in real-time. 

## FAQs

Can I update a stack to a different deployment type (Physical, Virtual) or dataflow option (Option1, 2a, 2b)? 
- Updates are currently not supported. To achieve a different deployemnt type or dataflow type, you'll need to deploy a new stack. 

Can I deploy multiple times in the same AWS account? 
- Yes, you may deploy multiple stacks in the same account. Be aware that data ingestion pipelines are not deployment specific. This means if both a "Virtual Option 1" and "Virtual Option 2a" deployment exists, data from the "Virtual Option 1" deployment will appear in the "Virtual Option 2a" S3 bucket. To temporarily prevent this, you may disable the IoT Rules associated with the deployment you no longer want to receive data from. Find the IoT Rules associated with a specific deployment by the CloudFormation stack name. 

How do I delete a prior deployment?
- Navigate to the CloudFormation console and delete the base stack (not the stack named "nested"), in order to clean up the account as much as possible.
- Depending on the health of the stack, the deletion will fail due to non-empty S3 buckets and a deployed Greengrass Group. Empty the S3 buckets, force a reset of the Greengrass group, then navigate back to the CloudFormation console and once again delete the base stack. 
- Other resources to clean up after stack deletion (if desired): IoT SiteWise Portal, IoT SiteWise Gateway, Iot SiteWise Models and Assets, QuickSight dataset.

## Troubleshooting

Quarantined certificate in Ignition doesn't show up for Option 1 deployments
- Navigate to the "Gateways" in the IoT SiteWise console, find the Gateway associated with your deployment (compare to the Greengrass Group ID if required), hit "Edit" then hit "Save". Look out for the Quarantined certificate in the Ignition console. 

