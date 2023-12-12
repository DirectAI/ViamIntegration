# DirectAI Viam Integration (beta)
Module of the Viam vision service to automatically build, deploy, and run inferences on custom object detectors and image classifiers via DirectAI's cloud offering. Since this is a beta test of such a service, the latency is high and availability of the cloud service is not guaranteed.

Internally, this module calls DirectAI's `deploy_detector` and `deploy_classifier` endpoints with the provided configuration, saves the ID of the deployed models, and then calls the models via their IDs on incoming images. See [docs](https://api.alpha.directai.io/docs) for an overview of DirectAI's publicly available API.

## Getting started

The first step is to obtain DirectAI API credentials. Instructions [here](https://api.alpha.directai.io/docs).

This module implements the following methods of the [vision service API](https://docs.viam.com/services/vision/#api):
  * `GetDetections()`
  * `GetDetectionsFromCamera()`
  * `GetClassifications()`
  * `GetClassificationsFromCamera()`

> [!NOTE]  
> Before configuring your vision service, you must [create a robot](https://docs.viam.com/manage/fleet/robots/#add-a-new-robot).

## Configuration

Navigate to the **Config** tab of your robot’s page in [the Viam app](https://app.viam.com/). Click on the **Services** subtab and click **Create service**. Select the `vision` type, then select the `directai-beta` model. Enter a name for your service and click **Create**.

### Example Configuration

### TODO: add example configuration

> [!NOTE]  
> For more information, see [Configure a Robot](https://docs.viam.com/manage/configuration/).

### Attributes

The following attributes are available for `directai:viamintegration:directai-beta` vision services:

### Example Viam Configuration

DirectAI module Viam vision service sample configuration:

[DirectAI Viam Vision Service Config](viam_service_config.json.template)


Viam transform camera sample configuration:

[Viam Transform Camera Config](viam_transform_camera_config.json.template)


### Example Access JSON

```json
{
  "DIRECTAI_CLIENT_ID": "UE9S0AG9KS4F3",
  "DIRECTAI_CLIENT_SECRET": "L23LKkl0d5<M0R3S4F3"
}
```
