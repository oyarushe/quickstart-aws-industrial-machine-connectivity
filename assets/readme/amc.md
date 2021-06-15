## Asset Model Converter

The asset model converter (AMC) code is in two separate lambda functions located in the functions/source directory of the repository.

* AssetModelIngestion

    This is the ingestion lambda. It’s purpose is to listen to MQTT messages coming from the CirusLink Ignition module and put them into the incoing S3 bucket as objects. The relevant handler file is “assetModelIngestion.py”. 

* AssetModelConverter
    
    The AMC really covers two functions – AMC1, and AMC2. 
        
    * AMC1 
        * This code is triggered via an S3 Object Creation trigger from the incoming bucket. It has it’s reserved concurrent executions set to 1, to ensure that only a single instance of the lambda can ever fire at once. This has been done because the Ignition CirrusLink module can birth the asset structure as multiple discrete MQTT messages, each of which become file objects in S3.
        * The core logic of the AMC1 comes in the form of the main handler file, `assetModelConverter.py` It contains the base lambda handler function, which in turn calls into the AssetModelConverter class to execute the handling of a given S3 object creation event. This code in turn calls the relevant Driver code to handle the asset structure files.
        * AMC Drivers - AMC Drivers in AMC1 are responsible for parsing the incoming asset structure file(s), and converting it into a normalized format that is then stored into DynamoDB. Please see the ‘Creating AMC Drivers’ section of the Getting Started guide for more details on creating drivers, and the DynamoDB normalized format.

    * AMC2
        * This relevant code file here is ‘createSitewiseResources.py’ This contains code to take the normalized DynamoDB format, and create relevant AWS IoT Sitewise assets and models from that format. Changes are marked in the DynamoDB table to various assets/models that require updates/creation.
        * Additionally, all AWS IoT Sitewise interactions take place in the `sitewiseUtils.py` code.

            > Please note that only additive changes are supported at this time.

        * The AMC2 process comes in the form of the following steps:

            1. Model Creation - The DynamoDB models table is queried to look for models that require creation. Those are created in AWS IoT Sitewise.
            2. Asset Creation - The DynamoDB assets table is also queries, looking for records that are marked as needing creation. Those assets, instances of the models created during ‘Model Creation’ are then created in AWS IoT Sitewise.
            3. Model Hierarchies - In this step Models are associated with each other in a hierarchy that are tagged as having such a parent/child relationship.
            4. Asset Associations - In this final step, assets that are tagged as having a parent/child relationship are associated with each.

### Creating AMC Drivers

Following are the instructions to create AMC drivers.

1. Write the driver that interprets the incoming hierarchy data from your edge-based asset modeling software and converts it into the AMC-approved format (see the format here) and puts it into DynamoDB
    1. Refer to the template file for guidance while writing your driver:
        
        `/functions/source/AssetModelConverter/drivers/example_driver_template.py`
    2. Highly recommended – also refer to the existing drivers: 
            
        `/functions/source/AssetModelConverter/drivers/igniitonCirrusLinkDriver.py`
            
        `/functions/source/AssetModelConverter/drivers/ignitionFileDriver.py`
            
        `/functions/source/AssetModelConverter/drivers/kepserver_file_driver.py`
2. Edit the entry point file for the AMC (`/functions/source/AssetModelConverter/assetModelConverter.py`) to use your new driver:
    1. Import your driver with import statement:
        
        `From drivers.[name_of_file] import [name_of_driver_class]`
    2. Add your driver to the ‘driverTable’ list
        
        `[name_of_driver]:[name_of_driver_class]`
3. Replace the AssetModelConverter zip file with its new contents:
    1. Zip up the contents of `/functions/source/AssetModelConverter/`
    2. Name the zip file above `AssetModelConverter.zip`
    3. Replace the old `AssetModelConverter.zip` file (`/functions/packages/AssetModelConverter/AssetModelConverter.zip`) with the new `AssetModelConverter.zip` file you created above. 
4. Edit the CloudFormation template to include your driver’s name: `/templates/IMC-workload.template.yaml`
    * Add an item to the list of AMCDrivers (parameter section):
        
        `- [name_of_driver_here]`

