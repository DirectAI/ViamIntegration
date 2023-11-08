# aws-sagemaker
Module of the Viam vision service to access models deployed on cloud endpoints using AWS Sagemaker.  This module allows you to access vision ML models that have been deplo

## Getting started

The first step is to deploy your model to the AWS Sagemaker endpoint. You can do this programmatically or through the AWS console. Instructions [here](https://docs.aws.amazon.com/sagemaker/latest/dg/deploy-model.html).

This module implements the following methods of the [vision service API](https://docs.viam.com/services/vision/#api):
  * `GetDetections()`
  * `GetDetectionsFromCamera()`
  * `GetClassifications()`
  * `GetClassificationsFromCamera()`

> [!NOTE]  
> Before configuring your vision service, you must [create a robot](https://docs.viam.com/manage/fleet/robots/#add-a-new-robot).

## Configuration

Navigate to the **Config** tab of your robot’s page in [the Viam app](https://app.viam.com/). Click on the **Services** subtab and click **Create service**. Select the `vision` type, then select the `aws-sagemaker` model. Enter a name for your service and click **Create**.

### Example Configuration

```json
{
  "modules": [
    {
      "type": "registry",
      "name": "viam_aws-sagemaker",
      "module_id": "viam:aws-sagemaker",
      "version": "0.0.1"
    }
  ],
  "services": [
    {
      "name": "myVisionModule",
      "type": "vision",
      "namespace": "rdk",
      "model": "viam:vision:aws-sagemaker",
      "attributes": {
        "access_json": "/Users/myname/Documents/accessfile.json",
        "endpoint_name": "jumpstart-dft-tf-ic-efficientnet-b1-classification-1",
        "aws_region": "us-east-2",
        "source_cams": [
          "myCam1",
          "myCam2"
        ]
      }
    }
  ]
}

```

> [!NOTE]  
> For more information, see [Configure a Robot](https://docs.viam.com/manage/configuration/).

### Attributes

The following attributes are available for `viam:vision:aws-sagemaker` vision services:

| Name | Type | Inclusion | Description |
| ---- | ---- | --------- | ----------- |
| `endpoint_name` | string | **Required** | The name of the endpoint as given by AWS. |
| `aws_region` | string | **Required** | The name of the region in AWS under which the model can be found. |
| `access_json` | string | **Required** | The on-robot location of a JSON file that contains AWS access credentials [(see below)](#example-access-json). |
| `source_cams` | array | **Required** | The names of the camera(s) you have configured on your robot that may be used as input for the vision service. |

### Example Access JSON

```json
{
  "access_key": "UE9S0AG9KS4F3",
  "secret_access_key": "L23LKkl0d5<M0R3S4F3"
}
```
