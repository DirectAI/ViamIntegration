from io import BytesIO
from typing import ClassVar, List, Mapping, Sequence, Any, Dict, Optional, Union, cast
from typing_extensions import Self
from PIL import Image

from viam.components.camera import Camera
from viam.media.video import RawImage, CameraMimeType
from viam.proto.service.vision import Classification, Detection
from viam.services.vision import Vision
from viam.module.types import Reconfigurable
from viam.proto.app.robot import ServiceConfig
from viam.proto.common import PointCloudObject, ResourceName
from viam.resource.base import ResourceBase
from viam.resource.types import Model, ModelFamily
from viam.utils import ValueTypes
from viam.logging import getLogger
from google.protobuf.json_format import MessageToDict
import logging
LOGGER = getLogger(__name__)

import json
import requests
import base64
import httpx
import asyncio


def get_access_token(base_url, client_id, client_secret):
    params = {
        "client_id": client_id,
        "client_secret": client_secret
    }
    response = requests.post(base_url + "/token", params=params)
    
    return response.json()['access_token']


class DirectModel(Vision, Reconfigurable):
    """
    DirectModel implements a vision service that only supports detections
    and classifications.

    It inherits from the built-in resource subtype Vision and conforms to the
    ``Reconfigurable`` protocol, which signifies that this component can be
    reconfigured. Additionally, it specifies a constructor function
    ``DirectModel.new_service`` which confirms to the
    ``resource.types.ResourceCreator`` type required for all models.
    """

    # Here is where we define our new model's colon-delimited-triplet
    # (viam:vision:aws-sagemaker) viam = namespace, vision = family, aws-sagemaker = model name.
    MODEL: ClassVar[Model] = Model(ModelFamily("directai", "viamintegration"), "directai-beta")

    def __init__(self, name: str):
        super().__init__(name=name)
        self.async_http_client = httpx.AsyncClient()
        self.http_client = httpx.Client()

    async def cleanup(self):
        self.http_client.close()
        self.async_http_client.aclose()

    # Constructor
    @classmethod
    def new_service(cls,
                 config: ServiceConfig,
                 dependencies: Mapping[ResourceName, ResourceBase]) -> Self:
        service = cls(config.name)
        service.reconfigure(config, dependencies)
        return service

    # Validates JSON Configuration
    @classmethod
    def validate_config(cls, config: ServiceConfig) -> Sequence[str]:
        config_dict = MessageToDict(config.attributes)
        
        access_json = config_dict.get("access_json", None)
        if access_json is None:
            raise Exception(
                "The location of the access JSON file is required as an attribute for a DirectAI service."
            )
        if access_json[-5:] != ".json":
            raise Exception(
                "The location of the access JSON must end in '.json'"
            )
        
        # TODO: add more in-depth validation
        
        LOGGER.log(logging.INFO, config_dict)
        
        return config.attributes.fields["source_cams"].list_value
    
    def reset_headers(self):
        token_params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        response = self.http_client.post(self.base_url + "/token", params=token_params)
        self.token = response.json()['access_token']
        self.headers = {
            'Authorization': f"Bearer {self.token}",
        }

    # Handles attribute reconfiguration
    def reconfigure(self,
                    config: ServiceConfig,
                    dependencies: Mapping[ResourceName, ResourceBase]):
        # TODO: add error handling

        config_dict = MessageToDict(config.attributes)
        
        with open(config_dict["access_json"], "r") as f:
            access_json = json.load(f)

        self.base_url = access_json.get("DIRECTAI_BASE_URL", "https://api.free.directai.io")
        self.client_id = access_json["DIRECTAI_CLIENT_ID"]
        self.client_secret = access_json["DIRECTAI_CLIENT_SECRET"]
        
        self.reset_headers()
        
        if "deployed_detector" in config_dict:
            self.nms_thresh = config_dict["deployed_detector"]["nms_threshold"]
            self.detector_configs = config_dict["deployed_detector"]["detector_configs"]
            
            detector_msg = {
                "detector_configs": self.detector_configs,
                "nms_thresh": self.nms_thresh
            }
            deploy_detector_response = self.http_client.post(
                self.base_url + "/deploy_detector",
                headers=self.headers,
                json=detector_msg
            )
            LOGGER.log(logging.INFO, deploy_detector_response.json())
            self.deployed_detector_id = deploy_detector_response.json()['deployed_id']
        else:
            LOGGER.log(logging.INFO, "No deployed detector in config")
            self.deployed_detector_id = None
            self.nms_thresh = None
            self.detector_configs = None
        
        if "deployed_classifier" in config_dict:
            self.classifier_configs = config_dict["deployed_classifier"]["classifier_configs"]
            
            classifier_msg = {
                "classifier_configs": self.classifier_configs
            }
            deploy_classifier_response = self.http_client.post(
                self.base_url + "/deploy_classifier",
                headers=self.headers,
                json=classifier_msg
            )
            LOGGER.log(logging.INFO, deploy_classifier_response.json())
            self.deployed_classifier_id = deploy_classifier_response.json()['deployed_id']
        else:
            LOGGER.log(logging.INFO, "No deployed classifier in config")
            self.deployed_classifier_id = None
            self.classifier_configs = None
        
        # example:
        """
        {
            "access_json": "directai_credentials.json",
            "deployed_detector": {
                "nms_threshold": 0.1,
                "detector_configs": [
                    {
                        "name": "head",
                        "examples_to_include": [
                            "head"
                        ],
                        "detection_threshold": 0.1
                    },
                    {
                        "name": "fist",
                        "examples_to_include": [
                            "fist"
                        ],
                        "examples_to_exclude": [
                            "open hand",
                            "hand"
                        ],
                        "detection_threshold": 0.1
                    }
                ]
            },
            "deployed_classifier": {
                "classifier_configs": [
                    {
                        "name": "kitchen",
                        "examples_to_include": [
                            "kitchen"
                        ],
                        "examples_to_exclude": []
                    },
                    {
                        "name": "living room",
                        "examples_to_include": [
                            "living room"
                        ],
                        "examples_to_exclude": []
                    },
                    {
                        "name": "bedroom",
                        "examples_to_include": [
                            "bedroom"
                        ],
                        "examples_to_exclude": []
                    },
                    {
                        "name": "office",
                        "examples_to_include": [
                            "office"
                        ],
                        "examples_to_exclude": []
                    },
                    {
                        "name": "bathroom",
                        "examples_to_include": [
                            "bathroom"
                        ],
                        "examples_to_exclude": []
                    }
                ]
            }
        }
        """
        
    """
    Implement the methods the Viam RDK defines for the vision service API
    (rdk:service:vision)
    """

    async def get_classifications(self,
                                 image: Union[Image.Image, RawImage],
                                 count: int,
                                 *, 
                                 extra: Optional[Dict[str, Any]] = None,
                                 timeout: Optional[float] = None,
                                 **kwargs) -> List[Classification]:
        assert self.deployed_classifier_id is not None, "No deployed detector!"
        
        classifications = []
        
        if isinstance(image, RawImage):
            content = image.data
            mime_type = image.mime_type
        else:
            stream = BytesIO()
            image = image.convert("RGB")
            image.save(stream, "JPEG")
            content = stream.getvalue()
            mime_type = "image/jpeg"
        
        files = {
            "data": ("test.jpg", content, mime_type)  # TODO: can we skip the stream?
        }
        classifier_params = {
            "deployed_id": self.deployed_classifier_id,
        }
        resp = await self.async_http_client.post(
            self.base_url + "/classify",
            params=classifier_params,
            files=files,
            headers=self.headers
        )
        j = resp.json()
        if resp.status_code == 401:
            LOGGER.log(logging.INFO, "DirectAI auth token expired, refreshing")
            self.reset_headers()
            resp = await self.async_http_client.post(
                self.base_url + "/classify",
                params=classifier_params,
                files=files,
                headers=self.headers
            )
            j = resp.json()
        
        # this time, raise on ANY error
        if resp.status_code != 200:
            raise ValueError(j)
        
        pairs = list(j["scores"].items())
        res = sorted(pairs, key = lambda x: -x[1]) # zipped in decreasing probability order
        for i in range(count):
            classifications.append({"class_name": res[i][0], "confidence": res[i][1]})
        
        return classifications

    async def get_classifications_from_camera(self, 
                                              camera_name: str, 
                                              count: int, 
                                              *,
                                              extra: Optional[Dict[str, Any]] = None,
                                              timeout: Optional[float] = None,
                                              **kwargs) -> List[Classification]:
        if camera_name not in self.source_cams:
            raise Exception(
                "Camera name given to method",camera_name, " is not one of the configured source_cams ", self.source_cams)
        cam = self.cameras[camera_name]
        img = await cam.get_image()
        return await self.get_classifications(image=img, count=count)
 
    async def get_detections(self,
                            image: Union[Image.Image, RawImage],
                            *,
                            extra: Optional[Dict[str, Any]] = None,
                            timeout: Optional[float] = None,
                            **kwargs) -> List[Detection]:
        assert self.deployed_detector_id is not None, "No deployed detector!"
        
        detections = []
        
        if isinstance(image, RawImage):
            content = image.data
            mime_type = image.mime_type
            # NOTE: DirectAI may return boxes that are out of bounds
            # to address this, we need the image size
            image = Image.open(BytesIO(content))
            width, height = image.size
        else:
            stream = BytesIO()
            image = image.convert("RGB")
            width, height = image.size
            image.save(stream, "JPEG")
            content = stream.getvalue()
            mime_type = "image/jpeg"
        
        files = {
            "data": ("test.jpg", content, mime_type)  # TODO: can we skip the stream?
        }
        detection_params = {
            "deployed_id": self.deployed_detector_id,
        }
        resp = await self.async_http_client.post(
            self.base_url + "/detect",
            params=detection_params,
            files=files,
            headers=self.headers
        )
        j = resp.json()
        if resp.status_code == 401:
            LOGGER.log(logging.INFO, "DirectAI auth token expired, refreshing")
            self.reset_headers()
            resp = await self.async_http_client.post(
                self.base_url + "/detect",
                params=detection_params,
                files=files,
                headers=self.headers
            )
            j = resp.json()
        
        # this time, raise on ANY error
        if resp.status_code != 200:
            raise ValueError(j)
        
        for det in j[0]:
            out_box = {
                "confidence": det["score"],
                "class_name": det["class"],
                "x_min": max(int(det["tlbr"][0]), 0),
                "y_min": max(int(det["tlbr"][1]), 0),
                "x_max": min(int(det["tlbr"][2]), width),
                "y_max": min(int(det["tlbr"][3]), height)
            }
            detections.append(out_box)
        
        return detections

    async def get_detections_from_camera(self,
                                        camera_name: str,
                                        *,
                                        extra: Optional[Dict[str, Any]] = None,
                                        timeout: Optional[float] = None,
                                        **kwargs) -> List[Detection]:


        if camera_name not in self.source_cams:
            raise Exception(
                "Camera name given to method",camera_name, " is not one of the configured source_cams ", self.source_cams)
        cam = self.cameras[camera_name]
        img = await cam.get_image()
        return await self.get_detections(image=img)
    
    async def get_object_point_clouds(self,
                                      camera_name: str,
                                      *,
                                      extra: Optional[Dict[str, Any]] = None,
                                      timeout: Optional[float] = None,
                                      **kwargs) -> List[PointCloudObject]:
        raise NotImplementedError
    
    async def do_command(self,
                        command: Mapping[str, ValueTypes],
                        *,
                        timeout: Optional[float] = None,
                        **kwargs):
        raise NotImplementedError
    

