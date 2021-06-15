## Post-deployment steps

The Post-deployment steps include the following:

1. [Edge Devices (Physical Deployments Only)](#edge-devices-(physical-deployments-only))
2. [Edge Software Deployment (Physical Deployments Only)](#edge-software-deployment-(physical-deployments-only))
3. [Driver Specific Configuration](#driver-specific-configuration)
4. [Update SiteWise Gateway](#update-sitewise-gateway)
5. [Validate Incoming Data](#validate-incoming-data)
6. [View SiteWise Portal Data](#view-sitewise-portal-data)

### Edge Devices (Physical Deployments Only)
The physical brownfield deployment is intended to demonstrate the capabilities of the IMC Quick Start in an environment where the end user has an existing edge-based asset modeling software (such as Ignition or KepServer). It is deployed onto physical hardware. After deployment, the physical hardware will run Greengrass software and connect into the edge-based asset modeling software. The IMC Quick Start supports the following OEM devices: 

* Lenovo
  * Model: ThinkCentre M90n IoT
  * Architecture: Intel® Celeron® 4205U (x86)
  * URL: https://www.lenovo.com/us/en/desktops-and-all-in-ones/thinkcentre/m-series-tiny/ThinkCentre-M90n-IoT/p/thinkcentre-m90n-iot
* ADLINK 
  * Model: MXE-211
  * Architecture: Intel Atom® Processor E3900 (x86) 
  * https://www.adlinktech.com/Products/Industrial_IoT_and_Cloud_solutions/IoTGateway/MXE-210_Series?lang=en
* OnLogic
  * Model: Karbon 300 Compact Rugged Computer
  * Architecture: Intel Atom® E3930 or E3950 processors
  * URL: https://onlogic.com/k300/ 
* Advantech 
  * Model: UNO-2372G
  * Architecture: Intel Atom E3845/Celeron® J1900 Quad-Core Processors
  * URL: https://www.advantech.com/products/1-2mlj9a/uno-2372g/mod_f4ff5680-f016-44bd-bff0-e5eddfd82237
* MOXA
  * Model: MC-1112-E4-T
  * Architecture: Intel Atom® Processor E3845 processor
  * URL: https://www.moxa.com/en/products/industrial-computing/x86-computers/mc-1100-series/mc-1121-e4-t

### Edge Software Deployment (Physical Deployments Only)
> This step is only necessary if deploying one of the physical deployment options (Physical-Greenfield/Physical-Brownfield)

> You must have the AWS CLI configured to point to the AWS account you’re using for the IMC Quick Start.

> The Physical-Brownfield deployment mode does not come with a configured set of project tags similar to the virtual deployment but does come with a set of device simulations that can be configured to represent a project tag structure similar to the virtual deployment tag structure (or your own structure entirely). This deployment can be configured to work with a physical PLC test harness. 

> The Physical-Greenfield deployment mode is compatible with either Inductive Automation’s Ignition Server (https://inductiveautomation.com/ignition/) or PTCs KEPServerEX (https://www.kepware.com/en-us/products/kepserverex/). This deployment option does not bootstrap any partner edge software. The only edge software application that is bootstrapped on the physical hardware as part of the deployment is AWS IoT Greengrass.


#### Retrive the IMC Edge Device Bootup Script

Retrieve and run the bootup script for the physical hardware device

  1. Open a terminal on the physical hardware
  2. Use the command line to become the root user in your terminal session: 
 
        `sudo su`

  3. Ensure you are in the `home/ubuntu` directory
  4. Use the command line to retrieve the deployment script from your stack’s S3 bucket. Before running this commmand, ensure you have the AWS CLI configured in the region where you are launching the IMC Quick Start CloudFormation stack.
  5. In your home directory run this command to get the physical deployment bootup script from an S3 bucket:

        `aws s3api get-object --bucket [DependenciesBucket] --key [BootupScript]`
 
        To get the values of the 2 options:
    
        - [DependenciesBucket]
        - [BootupScript]

        Open the CloudFormation service console, open the *NESTED* IMC Quick Start CloudFormation stack, select the *Outputs* tab and follow the instructions below:

        | Key | Value |
        |-----|-------|
        |[DependenciesBucket]|Dependecies Bucket Name (see green text below for reference)|
        |[BootupScript]|Find key corresponding to your configuration: <br> - BootupScriptGreenfieldOption1 <br> - BootupScriptGreenfieldOption2a <br> - BootupScriptGreenfieldOption2b <br> - BootupScriptBrownfieldAllOptions <br> and select its value (see blue text below for reference)|

![\[DependenciesBucket\] and \[BootupScript\]](../../docs/images/DependenciesBucket.png)

#### Execute the IMC Edge Device Bootup Script

1. Use the command line to make the file executable: 
  
    `chmod +x [bootupSctipt].sh`

    `[bootupScript]` was fetched in the previous step using `aws s3api get-object` CLI command described above.

2. Open the CloudFormation service console, open the *NESTED* IMC Quick Start CloudFormation stack, select the *Outputs* tab and copy the bootup CLI command from the *Value* of the Key:Value pairs below:

    | Key | Value |
    |-----|-------|
    | FullScriptParamsGreenfield1and2a | Copy the command from the CloudFormation *Value* column <br> This option is for: deployment type = Physical-Greenfield, data flow option = Option 1 (OPC-UA to SiteWise) or Option 2a (MQTT to IoT Core)
    | FullScriptParamsGreenfield2b| Copy the command from the CloudFormation *Value* column <br> This option is for: deployment type = Physical-Greenfield, data flow option = Option 2b (MQTT to Greengrass to IoT Core)
    | FullScriptParamsBrownField | Copy the command from the CloudFormation *Value* column <br> This option is for: deployment type = Physical-Brownfield, data flow option = Option 1 (OPC-UA to SiteWise)>> or Option 2a (MQTT to IoT Core)>> or Option 2b (MQTT to Greengrass to IoT Core)|

    ![Physical Deployment Bootup Scripts](../../docs/images/BootupCommand.png)

    - In the command string, replace `[HardwareIP]` with the physical device’s private IP address

    - Use the command line to run the deployment script, which should resemble something like the following (but filled in with your stack-specific values):
 
        `./physical-greenfield-option1.sh imc-snow-devicesbucketresource-4wjvs58vbhwj SnowCone/SnowConeCore.tar.gz 6tppoqlka4 us-east-1 SnowCone [Hardware-IP] SnowCone/SnowConeDevice.tar.gz [IoT Core ATS Endpoint]`

### Driver specific configuration

If you are using Ignition software, click the following link to see the [Ignition specific configuration steps](./ignition.md).


### Update SiteWise Gateway

1. Navigate to AWS IoT SiteWise console and in the left-hand menu select "Edge" -> "Gateways"
2. Select the gateway created during the stack launch. The gatweway name will follow the naming convention: 
    `[name_of_stack]_Automated_Gateway`
3. Click “Edit” in the Source Configuration for Automated Gateway Config” section
4. Click “Save” at the bottom. You do not need to make any changes. The action of editing and saving the configuration refreshes the SiteWise gateway and ensures data flows from the OPC UA server through the SiteWise gateway connector and into the AWS IoT SiteWise service in the AWS cloud.

### Validate Incoming Data 

#### Data Flow Option 1

When using Data Flow Option 1, verify data flowing into AWS IoT SiteWise

1. Now that you've trusted the SiteWise gateway connector certificate, return to the AWS IoT SiteWise console.
2. In the SiteWise console, click the menu icon on the left-hand side of the page and select "build" -> "assets"
3. In the asset tree on the left, drill down to an asset (i.e. Hauloff or Conveyor), select it and then select the “Measurements” tab for that asset.
4. Verify that the values in the “Latest value” column are updating. This indicates that the Ignition simulation of those virtual devices and sensors is properly sending data through to the SiteWise connector (via OPC UA) in Greengrass and up to AWS IoT SiteWise in the AWS cloud.

#### Data Flow Option 2a or 2b

Validate data flow into AWS IoT Core:

* Validate the data is flowing into the IoT Core on the topic configured within the edge application.

Validate data flow into S3:

1. Navigate to the S3 console.
2. Search for the bucket: *[stack_name_here]-imcs3bucket-[hash]*
3. Click the bucket and confirm that an S3 prefix inside the bucket named `mqtt` exists. 

### View SiteWise Portal Data 

>SSO must be enabled in the region your launched in the CloudFormation stack in and you must have a user created in that region in order to access the SiteWise Monitor dashboards in the following sections.

1. Log in to SiteWise Monitor Portal
    1. Navigate to the SiteWise console, select the icon on the left and select "Monitor" -> "Portals". 
    2. Select the hyperlinked "name" of the Portal most recently added (the topmost on the list). 
    3. Add yourself as an administrator of the Portal by clicking “Assign Users” in the Portal Administrators section
    4. Once you are listed as a Portal Administrator, click the hyperlinked URL in the Portal details section under the “URL” column. This URL should have the format: 

        `https://[XXXXX....XXXXXX].app.iotsitewise.aws.`

    5. Log in with the credentials (username and password) you just created for your administrator account.

2. View Data in SiteWise Monitor Portal
    1. Select “Dashboards” tab on the left-hand side, then select the newly created dashboard hyperlink under the “Name” column of the Dashboards page.
    2. Data should be flowing into the line charts for the asset measurement properties
    3. You can also see data for individual assets by navigating to the “Asset Library” tab on the left and selecting an asset from the asset tree. Once an asset is selected, you can view its properties.
