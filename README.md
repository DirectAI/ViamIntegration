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

On the new component panel, copy and paste the Example Detector *or* Classifier Attributes.

### Example Detector Attributes

```json
{
  "access_json": "ABSOLUTE_PATH_TO_ACCESS_JSON_FILE",
  "deployed_detector": {
    "detector_configs": [
      {
        "name": "nose",
        "examples_to_include": [
          "nose"
        ],
        "detection_threshold": 0.1
      },
      {
        "examples_to_include": [
          "mouth"
        ],
        "examples_to_exclude": [
          "mustache"
        ],
        "detection_threshold": 0.1,
        "name": "mouth"
      },
      {
        "examples_to_include": [
          "eye"
        ],
        "detection_threshold": 0.1,
        "name": "eye"
      },
    ],
    "nms_threshold": 0.1
  }
}
```

### Example Classifier Attributes

```json
{
  "access_json": "ABSOLUTE_PATH_TO_ACCESS_JSON_FILE",
  "deployed_classifier": {
    "classifier_configs": [
      {
        "name": "happy",
        "examples_to_include": [
          "happy person"
        ],
      },
      {
        "name": "sad",
        "examples_to_include": [
          "sad person"
        ]
      }
    ]
  }
}
```

### Example Access JSON

Your Access JSON should be stored on the machine that's running your Viam Server. Ensure that the Access JSON path that you provide in your Config (shown above) is **absolute**, not relative. (e.g. `/Users/janesmith/Downloads/directai_credential.json`, not `~/Downloads/directai_credential.json`) You can access your credentials by clicking **Get API Access** on the [DirectAI website](https://directai.io/).

```json
{
  "DIRECTAI_CLIENT_ID": "UE9S0AG9KS4F3",
  "DIRECTAI_CLIENT_SECRET": "L23LKkl0d5<M0R3S4F3"
}
```

### Attributes

The following attributes are available for `directai:viamintegration:directai-beta` vision services:
| Name | Type | Inclusion | Description |
|------|------|-----------|-------------|
| `access_json` | string | **Required** | A string that indicates an absolute path on your local machine to a JSON including DirectAI Client Credentials. See description in [Example Access JSON](#example-access-json) section. |
| `deployed_classifier` | json | **Optional** | A JSON that contains a `classifier_configs` key and corresponding list of classifier configurations. Each classifier is defined by a `name`, a list of text `examples_to_include`, and a list of text `examples_to_exclude`. See [Example Classifier Attributes](#example-classifier-attributes). |
| `deployed_detector` | json | **Optional** | A JSON that contains a `detector_configs` key and corresponding list of detector configurations. Each detector is defined by a `name`, a list of text `examples_to_include`, and a list of text `examples_to_exclude`. See [Example Detector Attributes](#example-detector-attributes). |

> [!NOTE]  
> For more information, see [Configure a Robot](https://docs.viam.com/manage/configuration/).








