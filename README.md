# CodePipeline Lambda Function for Integration with Checkmarx One and Pivotal Tracker

## Create SSM Parameters
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
    Do the same for  /Checkmarx/CxOneServerURL, /Checkmarx/CxOneIamURL, /Checkmarx/CxOneTenantName, /PivotalTracker/Token


#### AWS CLI:
```commandline
aws ssm put-parameter --name /Checkmarx/CxOneServerURL --type SecureString --value "xxxxxx"
aws ssm put-parameter --name /Checkmarx/CxOneIamURL --type SecureString --value "xxxxxx"
aws ssm put-parameter --name /Checkmarx/CxOneTenantName --type SecureString --value "xxxxxx"
aws ssm put-parameter --name /Checkmarx/CxOneAPIKey --type SecureString --value "xxxxxx"
aws ssm put-parameter --name /PivotalTracker/Token --type SecureString --value "xxxxxx"
```

## Create AWS S3 bucket
bucket name: cxone-pivotal-tracker

## Create AWS IAM policy

Policy name: CheckmarxCodePipelineLambdaSSM 

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "codepipeline",
            "Effect": "Allow",
            "Action": [
                "codepipeline:PutJobSuccessResult",
                "codepipeline:PutJobFailureResult"
            ],
            "Resource": [
                "*"
            ]
        },
        {
            "Sid": "SystemManager",
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter",
                "ssm:GetParametersByPath",
                "ssm:GetParameters"
            ],
            "Resource": [
                "*"
            ]
        },
        {
            "Sid": "KMS",
            "Effect": "Allow",
            "Action": [
                "kms:Decrypt"
            ],
            "Resource": [
                "*"
            ]
        },
        {
            "Sid": "Lambda",
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                "*"
            ]
        }
    ]
}
```

## Create AWS IAM Role

Trusted entity type:  AWS service, choose service *Lambda*

add below permissions (policies):
* AWSLambdaBasicExecutionRole
* CheckmarxCodePipelineLambdaSSM

Role name: LambdaCodePipelineSSMExecutionRole

## Create Lambda Function

1. prepare the deployment
   * get the Lambda source code `git clone https://github.com/HappyY19/CxOneIntegrationWithPIvotalTracker.git`
   * go to the directory `cd CxOneIntegrationWithPIvotalTracker` 
   * create a Python virtual environment `python3 -m venv venv`
   * activate virtual environment `source ./venv/bin/activate`
   * install dependencies `pip install -r requirements.txt`
   * Use pip show to find the location in your virtual environment where pip has installed your dependencies. `pip show boto3` The folder in which pip installs your libraries may be named site-packages or dist-packages. This folder may be located in either the lib/python3.x or lib64/python3.x directory (where python3.x represents the version of Python you are using).
   * Deactivate the virtual environment `deactivate`
   * Navigate into the directory containing the dependencies you installed with pip and create a .zip file in your project directory with the installed dependencies at the root. `cd venv/lib/python3.10/site-packages` `zip -r ../../../../CxScan.zip .`
   * Navigate to the root of your project directory where the .py file containing your handler code is located and add that file to the root of your .zip package.  `cd ../../../../`  `zip CxScan.zip lambda_function.py  -r utilities/`
   * The CxScan.zip file is what we need to upload to Lambda Function

2. create lambda function
   * Set name as CxScan, select runtime python 3.11, architecture x86_64, using an existing role, select the above AWS IAM Role *LambdaCodePipelineSSMExecutionRole*, then click button *Crate function*
   * In the code pane, click the dropdown button *Upload from*, select *.zip file*, then upload the CxScan.zip file
   * Go to *Configuration* pane, Set Lambda function time out to be 5 minutes

## Create the AWS CodePipeline

1. Choose pipeline Settings:
   * pipeline name, set a pipeline name, for example: cxone-pipeline. 
   * Service Role, New service role, set a Role name, enable Allow AWS CodePipeline to create a service role so it can be used with this new pipeline.
   * under Advanced Settings, choose *Custom Location*, type the S3 bucket name *cxone-pivotal-tracker*, use the *Default AWS Managed Key*

2. Add source stage

3. Add build stage
   you can skip this one

4. Add deploy stage
   * Deploy provider, choose Amazon s3
   * Bucket, choose the above bucket *cxone-pivotal-tracker*
   * S3 object key, set your source code zip file name, for example, "SampleApp.zip"

   Click button *Create pipeline*

5. edit the above pipeline, add a new stage
   * click button *Add stage*
   * fill in the stage name
   * click button *Add action group*
   * fill in the action name, for example, CxSCan,
   * Action Provider, *AWS Lambda*
   * Input artifacts, *SourceArtifact*
   * Function Name, select *CxScan*
   * User parameters, file in *{"project", "<Your-Project-Name>"}*
   * click button *Done*
   * *Save* the pipeline


## Run the pipeline
   * click the button *Release change*, then *Release*
