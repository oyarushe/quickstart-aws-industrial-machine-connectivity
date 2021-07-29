# Overview

**Connectors** are a set of technologies that allow users to connect source system information to _Element Unify_ or publish _Element Unify_ data to destination systems.

## Connector Framework

**Connectors** are built using **Unify SDKs**, which allow for streamlined interactions with _Element Unify_ APIs. For example, the **Unify Python SDK** is a Python library for developers to connect to and interact with _Element Unify_ endpoints including templates, datasets, pipelines, and organizations, without having to write code to interact directly with HTTP/REST APIs.

The **Connector Framework** allows developers to create custom connectors. The **Connector Framework** extends the capabilities of the **Unify SDK** with built-in functionality that streamlines connecting to other systems such as health metrics and scheduling. These custom connectors connect information from source systems and transmit the data to _Element Unify_, allowing the information from integrated source systems to be contextualized and integrated with other datasets, and made ready for downstream consumption. The **Connector Framework** currently supports Python. Developers should be familiar with standard Python development best practices, tools such as `Git` and `pip`.

It is recommended that developers review the existing Unify connectors for Ignition and KEPServerEX. Documentation can be found [here](unify-connectors.md).

## Deployment Options

Connectors for AWS are deployable to AWS as AWS Lambda via CloudFormation templates. Scheduling is handled through built-in Lambda capabilities.

# Getting Started

This section describes steps to develop and then deploy a custom connector with sample code.

## Install Prerequisites

Install the **Unify Connector Framework** and **Unify CLI** using `pip`:

    pip install unify-connector-framework
    pip install unify-cli

The Unify Connector Framework contains methods for the connector to interact with Element Unify. The Unify CLI allows developers to create a service account that the connector will use for authentication.

# Register Connector

**Connectors** use dedicated service accounts. As part of the connector registration, you will need to create a new service account. This can be done in two ways:

  1. Use **Unify CLI**

  2. Use a curl command.

## Option 1: Set Up Service Account With Unify CLI

Register for a new service account using the **Unify CLI**. If you have already set up a connection with the **Unify CLI**, skip the next section and go to the "Create New Service Account" section.

### Set Up Connection

If this is the first time using the **Unify CLI**, first add your Unify instance and then log in.

    unify cluster add

You will be prompted for information

  | Parameter | Description |
  | ----------- | ----------- |
  | Remote | Hostname of your _Element Unify_ instance. For example: https://app001-aws.elementanalytics.com/ |
  | Username | Your _Element Unify_ username (email) |
  | Password | Your _Element Unify_ password |
  | Name | Name of the connection |

Check to confirm the connection has been added

    unify cluster list

### Create New Service Account

First, log in to _Element Unify_ via **CLI** if you have not already.

    unify cluster login --remote [name of connection]

Next, create the new service account

    unify user addserviceaccount

The **CLI** will return the credentials for the new service account. Save this information for later.

## Option 2: Set Up Service Account with CURL

Run the command below to create a new service account. This command makes a `POST` request to the target _Element Unify_ organization to create the service account, and returns the service account information to the client. Update the information in brackets with _Element Unify_ hostname, credentials, and connector identifiers.

    curl -X POST "<YOUR HOSTNAME>/api/v1/orgs/<ORGANIZATION ID>/machine_users" -H "accept: application/json" -H "x-auth-token:*" -H "Content-Type: application/json" -H "x-organization-id:<ORGANIZATION ID>" -d '{"fullName":"<NAME OF SERVICE ACCOUNT>", "identifier":"<NAME OF CONNECTOR>","password":"<YOUR PASSWORD>","roleNames":["Contributor"]}'

# Instantiate Connector

This section describes steps to import required libraries and instantiate a new connector instance.

## Import Connector Framework Library:

First, create a new python file, such as `custom-connector.py`. Add the below code to import the connector library:

    from unifyconnectorframework.connector import Connector as UnifyConnector

## Set Up Connector Object

Create a new instance of the `UnifyConnector` object. The `UnifyConnector` object has methods to communicate with _Element Unify_ and accepts the service account credentials and target. Pass the credentials of the service account that was created during the registration process.

    serviceaccount = <Element Unify service account name>
    password = <Element Unify service account password>
    org_id = <Element Unify organization id>
    hostname = “https://app001-aws.elementanalytics.com/”
    connector_id = <Element Unify connector id>
    connector_label = <Custom tag for connector>
    connector_version = <Connector version>
    unify_connector = UnifyConnector(serviceaccount, password, org_id, hostname, connector_id, connector_label, connector_version)

# Upload Tag and Template Definitions to Element Unify

This section provides examples to connect tag definitions and template definitions to _Element Unify_.

## Upload Templates

Template definitions are split into two variables. One handles template and attribute definitions (`content_templates`). The second handles configuration parameters for templates and attributes (`content_template_params`). These variables are defined as strings in **CSV** format. To connect to actual systems, use appropriate libraries and create a reader to read the data into a string variable in **CSV** format. Commas (`,`) are used as delimiters and `\n` is used for new lines.

The `upload_template` and `upload_template_configuration` methods will create and append the templates and configuration parameters to the **Element Unify Template Library**.

Upload templates and attributes to **Element Unify Template Library**

    content_templates = [\
    “Template Name,Attribute,Type,UoM,Attribute Type”,\
    “Pump,Flow Rate,Double,gal/min,Continuous Value”,\
    “Pump,Motor,Motor,,Static”,\
    “Pump,FLOC,String,,Static”,\
    “Motor,Rotation Speed,Double,rpm,Continuous Value”]
    unify_connector.upload_template(“\n”.join(content_templates))


Upload template and attribute configuration parameters to **Element Unify Template Library**

    content_template_params = [\
    “template,attribute,key,value”,\
    “Pump,Flow Rate,Property Type,Measurement”,\
    “Pump,FLOC,Property Type,Attribute”,\
    “Pump,FLOC,Default Value,Pump ID”]
    unify_connector.upload_template_configuration(“\n”.join(content_template_params))

## Upload Datasets

Next, upload tag definitions or asset models to the **Dataset Catalog**. The definition or model is captured as a string. Commas (`,`) are used as delimiters and `\n` is used for new lines. The `create_dataset` method will upload the data as a dataset in _Element Unify’s_ dataset catalog. The method also returns a `data_set_id` key, which captures the `id` of the new dataset.


Upload datasets to **Element Unify Dataset Catalog**

    dataset_name = “tags_definition.csv”
    Content_assets = [\
    “Name,description,engunits,type”,\
    “FIC10102.PV,Flow Rate Pump-234,psi,float32”,\
    “SI10102.PV,Rot speed Motor-234,rpm,float32”]
    dataset_id = unify_connector.create_dataset(dataset_name, “\n”.join(content_assets))['data_set_id']

## Append New Data to Dataset

If you need to append data to update the existing dataset, use the `append_dataset` method. This will append new rows to the existing dataset referenced by `dataset_id`. The headers must be the same.

Upload datasets to **Element Unify Dataset Catalog**

    dataset_name = “tags_definition.csv”
    content_assets = [\
    “Name,description,engunits,type”,\
    “FIC20102.PV,Flow Rate Pump-334,psi,float32”,\
    “SI20102.PV,Rot speed Motor-334,rpm,float32”]
    unify_connector.append_dataset(dataset_id, “\n”.join(content_assets))

A full list of available methods is found in the **Connector Framework Reference Guide** found inside Element Unify Developer Portal.

### Deploy Connector as part of IMC

Then update the UnifySourceIngest/lambda_function.py to 1) include the module, 2) add a s3 key prefix, and 3) call the connector when a file is uploaded into the key prefix location

#### Include library

- At the top of UnifySourceIngest/lambda_function.py, import your library
    
      from [custom-connector].[connector] import [connector]

#### Add Key Prefix

- Add a key prefix variable

      [connector]_folder = '[key prefix]/'

#### Call connector in process_folder

- Pass Unify secrets to connector

      if (keyPrefix == [connector]_folder):
        connector = [Connector](secret.user_id, secret.password, secret.org_id, secret.cluster, False, True)

- Call ingest method

      connector.ingest([object_data], site_name, server_name, labels)
