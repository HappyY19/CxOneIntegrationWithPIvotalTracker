# CodePipeline Lambda Function for Integration with Checkmarx One and Pivotal Tracker

## Prerequisites

### Create SSM Parameters
#### AWS UI:

    Go to AWS Systems Manager
    Application Management -> Parameter Store
    Create Parameter:
        Name: /Checkmarx/CxOneAPIKey
        Description: CxOne API key
        Tier: Standard
        Type: SecureString
        KMS KeySource: My Current Account
        KMS Key ID: alias/aws/ssm
        Value: first.last@company.com
    Do the same for Checkmarx URL (String) and Password (SecureString)

#### AWS CLI:
```commandline
aws ssm put-parameter --name /Checkmarx/CxOneServerURL --type SecureString --value "xxxxxx"
aws ssm put-parameter --name /Checkmarx/CxOneIamURL --type SecureString --value "xxxxxx"
aws ssm put-parameter --name /Checkmarx/CxOneTenantName --type SecureString --value "xxxxxx"
aws ssm put-parameter --name /Checkmarx/CxOneAPIKey --type SecureString --value "xxxxxx"
aws ssm put-parameter --name /PivotalTracker/Token --type SecureString --value "xxxxxx"

```
