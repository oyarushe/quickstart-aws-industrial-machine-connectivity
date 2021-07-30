## Element Unify AWS resources

The Element Unify asset modeling component of the IMC consists of a series of AWS resources to orchestrate the tag and model ingestion from source systems into Element Unify, model sync to AWS IoT SiteWise, and credential management. The Element Unify asset modeling components are listed below. If you are an ISV partner looking to develop a custom connector for Element Unify, refer to the [Unify Connector Development Guide](unify-connector-development-guide.md)

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
