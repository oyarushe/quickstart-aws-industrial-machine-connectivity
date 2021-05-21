## Element Unify AWS resources

The Element Unify asset modeling component of the IMC consists of a series of AWS resources to orchestrate the tag and model ingestion from source systems into Element Unify, model sync to AWS IoT SiteWise, and credential management. The Element Unify asset modeling components are listed below:

### Lambdas
- UnifySourceIngest (name: ***-UnifySourceIngest-***) - Main Lambda that will call specific Unify connector to read tag definition exports from edge devices (ie. Ignition or KepServerEx), and upload into Element Unify as asset templates and/or asset datasets.
- UnifySiteWiseIngest (name: ***-UnifySiteWiseIngest-***) -  Retrieve asset models and asset hierarchies from AWS IoT SiteWise, and upload into Element Unify as asset templates and asset datasets.
- UnifySiteWiseUpdater (name: ***-UnifySiteWiseUpdater-***) - Deploys Element Unify asset templates and asset datasets as AWS IoT SiteWise asset models and asset hierarchies. Sets property aliases for attributes and measurements, and asset model hierarchies. Logs AWS IoT SiteWise options that require manual, explicit deletion.
- UnifyServiceAccountHandler (name: ***-UnifyServiceAccountHandler-***) - Lambda to retrieve service account. Passes user credentials to target Element Unify organization, which returns a new service account credentials. Stores service account credentials in Secrets Manager.
### Secrets Manager
- Stores connection information to Element Unify (name: ***-UnifySecrets-***). Connectors authenticate with Element Unify with information stored in this secrets manager.
  -  Cluster - Hostname of the destination Element Unify. Format: https://***.elementanalytics.com/
  - Org_Id - Id of organization
  - User_id - User id of service account
  - Password - Password for service account
  - User_name - Display name for service account
### S3
  - UnifyIncomingBucket  (name: ***-unifyincomingbucket-***) - Store exports here
  - UnifyBucket (name: ***-unifybucket-***) - Persists last timestamps to identify when changes were made in Element Unify templates and datasets. Stored in object elementUnifyLastUpdated.json.

## Element Unify Connector Development Guide

### Overview:

- Unify Python SDK

  Python library for developers to connect to and interact with Element Unify endpoints. These include: Templates, datasets, pipelines, and organization management.

- Unify Connector Python SDK
  
  Python library for developers to create their own connectors. Connectors connect information from source systems and transmit the data to Element Unify, allowing the information from integrated source systems to be contextualized and integrated with other datasets, and made ready for downstream consumption.
  
  Developers should be familiar with standard Python development best practices and tools such as Git, pip, CI/CD.

### Building a new connector:

#### Install prerequisites:
- Clone this repository
  - In requirements.txt
    - Add common.organization
    - Add unify-sdk
  - Pip install -r requirements.txt

#### Instantiate connector

- Import Connector SDK

      from common.organiztion_client import OrganizationClient as UnifyConnector

- Instantiate connector

      unify_connector = UnifyConnector(user_name, password, org_id, cluster)

#### Asset templates
- Asset templates represent asset class definitions. Asset templates contain attribute templates representing sensors (AWS IoT SiteWise measurement properties), static information (AWS IoT SiteWise attribute properties).
- Structure
  - Template Name
    - Represents the name of the template. Equivalent to asset model name.
    - Required. Uploads will append or update to existing asset templates.
  - Attribute
    - Represents the name of the template attribute. Equivalent to asset model property name.
    - Optional. When no value is set, the template is treated as empty.
  - Type
    - Represents the data type of the attribute or recursive template (template contains another template relationship). Equivalent to AWS IoT SiteWise asset model hierarchies.
    - Required if attribute is defined.
    - Accepts Boolean|Integer|Double|String|{Template name}.
  - UoM
    - Represents the units of measure for sensors.
    - Optional.
  - Attribute Type
    - Specifies the type of attribute.
    - Required if attribute is defined.
    - Accepts Continuous Value|Static|Alarm.
- Methods
  - list_templates
    - Return:
      - List of templates
  - upload_template(template_csv)
    - Parameter:
      - template_csv (str): template definition csv as string
    - Return:
      - Response success or exception message
  - update_template_categories(template_id, template_name, version, categories)
    - Parameter:
      - Template_id (int): Id of existing template
      - Template_name (str): Name of existing template
      - Version (int): Version of the template
      - Categories (list of str): List of categories to set on templates

#### Asset template configuration

- Asset template configuration represents properties for asset template attributes. Uploads will append or update to existing asset template configuration.
- Structure
  - Template
    - Represents the name of the template. Equivalent to asset model name.
  - Attribute
    - Represents the name of the template. Equivalent to asset model property name.
  - Key
    - For AWS IoT SiteWise, represents the property type or default value on attribute properties.
    - Accepts:
      - Property Type|Default Value
    - Value
      - For Property Type, accepts Measurement|Attribute|Transform|Metric
      - If Property Type is Attribute, Default Value is required
- Method
  - upload_template(config_csv)
  - Parameter:
    - config_csv (str): Template configuration definition csv as string
  - Return:
    - Response success or exception message

#### Assets Dataset
- Datasets represent either a tag definition, an asset hierarchy, or other asset information, represented in tabular format.
- Structure
  - CSV format. First row is the header. Delimiter is “,”. New line represented with “\n”.
- Methods
  - list_datasets:
    - Return:
      - List of datasets in organization
  - create_dataset(name, dataset_csv)
    - Parameter:
      - name (str): Name of new dataset
      - dataset_csv (str): Dataset content csv as string
    - Return:
      - Dataset id
  - update_dataset(dataset_csv, dataset_name, dataset_id)
    - Parameter:
      - dataset_csv (str): Dataset content csv as string
      - dataset_name (str): Name of new dataset
      - dataset_id (str): Id of existing dataset
    - Return:
      - Dataset id
  - truncate_dataset(dataset_id)
    - Parameter:
      - dataset_id (str): Id of existing dataset
  - Return:
    - Response success or exception message
  - append_dataset(dataset_id, dataset_csv)
    - Parameter:
      - dataset_id (str): Id of existing dataset
      - dataset_csv (str): Dataset content csv as string
    - Return:
      - Success or exception message
  - update_dataset_labels(dataset_id, labels)
    - Parameter:
      - dataset_id (str): Id of existing dataset
      - labels (list of str): List of labels to set on datasets
    - Return:
      - Success or exception message

#### Example:

    from common.organiztion_client import OrganizationClient as UnifyConnector

    user_name = “xyz”
    password = “xyz”
    org_id = “1”
    cluster = “https://xyz.elementanalytics.com/”
    unify_connector = UnifyConnector(user_name, password,org_id,cluster)

    content_templates = [\
      “Template Name,Attribute,Type,UoM,Attribute Type”,\
      “Pump,Flow Rate,Double,gal/min,Continuous Value”,\
      “Pump,Motor,Motor,,Static”,\
      “Pump,FLOC,String,,Static”,\
      “Motor,Rotation Speed,Double,rpm,Continuous Value”]
    unify_connector.upload_template(“\n”.join(content_templates))

    Content_template_params = [\
      “template,attribute,key,value”,\
      “Pump,Flow Rate,Property Type,Measurement”,\
      “Pump,FLOC,Property Type,Attribute”,\
      “Pump,FLOC,Default Value,Pump ID”]
    unify_connector.upload_template_configuration(“\n”.join(content_template_params))

    dataset_name = “tags_definition.csv”
    Content_assets = [\
      “Name,description,engunits,type”,\
      “FIC10102.PV,Flow Rate Pump-234,psi,float32”,\
      “SI10102.PV,Rot speed Motor-234,rpm,float32”]
    unify_connector.create_dataset(dataset_name, content_assets)['data_set_id']

### Deployment

To deploy the new connector, you will need to update the UnifySourceIngest/lambda_function.py to 1) include the library, 2) add a s3 key prefix, and 3) call the connector when a file is uploaded into the key prefix location

#### Include library

- At the top of UnifySourceIngest/lambda_function.py, import your library
    
      from [ignition_file_connector].[connector] import [connector]

#### Add Key Prefix

- Add a key prefix variable

      [connector]_folder = '[key prefix]/'

#### Call connector in process_folder

- Pass Unify secrets to connector

      if (keyPrefix == [connector]_folder):
        connector = [Connector](secret.user_id, secret.password, secret.org_id, secret.cluster, False, True)

- Call ingest method

      connector.ingest([object_data], site_name, server_name, labels)
