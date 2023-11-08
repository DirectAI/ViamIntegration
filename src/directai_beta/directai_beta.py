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

from dotenv import load_dotenv
import os
load_dotenv()
DIRECTAI_CLIENT_ID = os.getenv("DIRECTAI_CLIENT_ID")
DIRECTAI_CLIENT_SECRET = os.getenv("DIRECTAI_CLIENT_SECRET")
DIRECTAI_BASE_URL = os.getenv("DIRECTAI_BASE_URL")


def get_access_token(base_url, client_id, client_secret):
    params = {
        "client_id": client_id,
        "client_secret": client_secret
    }
    response = requests.post(base_url + "/token", params=params)
    
    return response.json()['access_token']


class DirectModel(Vision, Reconfigurable):
    """
    AWS implements a vision service that only supports detections
    and classifications.

    It inherits from the built-in resource subtype Vision and conforms to the
    ``Reconfigurable`` protocol, which signifies that this component can be
    reconfigured. Additionally, it specifies a constructor function
    ``AWS.new_service`` which confirms to the
    ``resource.types.ResourceCreator`` type required for all models.
    """

    # Here is where we define our new model's colon-delimited-triplet
    # (viam:vision:aws-sagemaker) viam = namespace, vision = family, aws-sagemaker = model name.
    MODEL: ClassVar[Model] = Model(ModelFamily("directai", "vision"), "directai-beta")

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
        # endpoint_name = config.attributes.fields["endpoint_name"].string_value
        # if endpoint_name == "":
        #     raise Exception(
        #         "An endpoint name is required as an attribute for an AWS vision service.")
        # aws_region = config.attributes.fields["aws_region"].string_value
        # if aws_region == "":
        #     raise Exception(
        #         "The AWS region is required as an attribute for an AWS vision service.")
        # access_json = config.attributes.fields["access_json"].string_value
        # if access_json == "":
        #     raise Exception(
        #         "The location of the access JSON file is required as an attribute for an AWS vision service.")
        # if access_json[-5:] != ".json":
        #     raise Exception(
        #         "The location of the access JSON must end in '.json'")
        source_cams = config.attributes.fields["source_cams"].list_value
        
        # LOGGER.log(logging.INFO, "BANANAFISH")
        # LOGGER.log(logging.INFO, config.attributes)
        # LOGGER.log(logging.INFO, type(config))
        
        # config_dict = MessageToDict(config.attributes)
        # LOGGER.log(logging.INFO, config_dict)
    
        return source_cams
    

    # Handles attribute reconfiguration
    def reconfigure(self,
                    config: ServiceConfig,
                    dependencies: Mapping[ResourceName, ResourceBase]):
        # TODO: add error handling
                
        self.base_url = DIRECTAI_BASE_URL
        self.client_id = DIRECTAI_CLIENT_ID
        self.client_secret = DIRECTAI_CLIENT_SECRET

        token_params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        response = self.http_client.post(self.base_url + "/token", params=token_params)
        self.token = response.json()['access_token']
        self.headers = {
            'Authorization': f"Bearer {self.token}",
        }
        
        config_dict = MessageToDict(config.attributes)
        
        self.nms_thresh = config_dict["nms_threshold"]
        self.detector_configs = config_dict["detector_configs"]
        
        detector_msg = {
            "detector_configs": self.detector_configs,
            "nms_thresh": self.nms_thresh
        }
        deploy_response = self.http_client.post(
            self.base_url + "/deploy_detector",
            headers=self.headers,
            json=detector_msg
        )
        LOGGER.log(logging.INFO, deploy_response.json())
        self.deployed_detector_id = deploy_response.json()['deployed_id']
        
        # example:
        """
        {
  "hello": "world",
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
      "name": "airpods",
      "examples_to_include": [
        "airpods"
      ],
      "detection_threshold": 0.1
    },
    {
      "name": "nose",
      "examples_to_include": [
        "nose"
      ],
      "detection_threshold": 0.1
    },
    {
      "name": "eye",
      "examples_to_include": [
        "eye"
      ],
      "detection_threshold": 0.07
    },
    {
      "name": "mouth",
      "examples_to_include": [
        "mouth"
      ],
      "detection_threshold": 0.07
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
}"""
        
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
        classifications = []
        # if isinstance(image, RawImage):
        #     if image.mime_type in [CameraMimeType.JPEG, CameraMimeType.PNG]:
        #         response = self.client.invoke_endpoint(EndpointName=self.endpoint_name, 
        #                                            ContentType= 'application/x-image',
        #                                            Accept='application/json;verbose',
        #                                            Body=image.data) 
        #     else:
        #         raise Exception("Image mime type must be JPEG or PNG, not ", image.mime_type)

        # else:
        #     stream = BytesIO()
        #     image = image.convert("RGB")
        #     image.save(stream, "JPEG")
        #     response = self.client.invoke_endpoint(EndpointName=self.endpoint_name, 
        #                                            ContentType= 'application/x-image',
        #                                            Accept='application/json;verbose',
        #                                            Body=stream.getvalue())
            
        # # Package results based on standardized output 
        # out = json.loads(response['Body'].read())
        # labels = out['labels']
        # probs = out['probabilities']
        # zipped = list(zip(labels, probs)) 
        # res = sorted(zipped, key = lambda x: -x[1]) # zipped in decreasing probability order
        for i in range(count):
            # classifications.append({"class_name": res[i][0], "confidence": res[i][1]})
            classifications.append({"class_name": f"test_{i}", "confidence": 0.5/i})

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
        
        detections = []
        
        if isinstance(image, RawImage):
            # stream = BytesIO(image.data)
            content = image.data
            mime_type = image.mime_type
        else:
            stream = BytesIO()
            image = image.convert("RGB")
            image.save(stream, "JPEG")
            content = stream.getvalue()
            mime_type = "image/jpeg"
        
        # img_content = base64.b64encode(stream.getvalue()).decode("utf-8")
        
        # msg = {
        #     "file": {
        #         "filename": "test.jpg",
        #         "content": img_content,
        #         "type": mime_type
        #     },
        #     "detector_configs": self.detector_configs,
        #     "nms_thresh": self.nms_thresh
        # }
        
        # r = requests.post(self.base_url + "/run_detectors", json=msg, headers=self.headers)
        # j = r.json()
        
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
        if resp.status_code != 200:
            raise ValueError(j)
        
        for det in j[0]:
            out_box = {
                "confidence": det["score"],
                "class_name": det["class"],
                "x_min": int(det["tlbr"][0]),
                "y_min": int(det["tlbr"][1]),
                "x_max": int(det["tlbr"][2]),
                "y_max": int(det["tlbr"][3])
            }
            detections.append(out_box)
        
        return detections

        # if isinstance(image, RawImage):
        #     if image.mime_type in [CameraMimeType.JPEG, CameraMimeType.PNG]:
        #         decoded = Image.open(BytesIO(image.data))
        #         width, height = decoded.width, decoded.height
        #         response = self.client.invoke_endpoint(EndpointName=self.endpoint_name, 
        #                                            ContentType= 'application/x-image',
        #                                            Accept='application/json;verbose',  
        #                                            Body=image.data) 
        #     else:
        #          raise Exception("Image mime type must be JPEG or PNG, not ", image.mime_type)

        # else:
        #     width, height = float(image.width), float(image.height)
        #     stream = BytesIO()
        #     image = image.convert("RGB")
        #     image.save(stream, "JPEG")
        #     response = self.client.invoke_endpoint(EndpointName=self.endpoint_name, 
        #                                            ContentType= 'application/x-image',
        #                                            Accept='application/json;verbose',
        #                                            Body=stream.getvalue())
            
        # # Package results based on standardized output
        # out = json.loads(response['Body'].read())
        # boxes =  out['normalized_boxes']
        # classes= out['classes']
        # scores = out['scores']
        # labels = out['labels']
        # n = min(len(boxes), len(classes), len(scores))
        
        # for i in range(5):
        #     # xmin, xmax = boxes[i][0] * width, boxes[i][2] * width
        #     # ymin, ymax = boxes[i][1] * height, boxes[i][3] * height

        #     # detections.append({ "confidence": float(scores[i]), "class_name": str(labels[int(classes[i])]), 
        #                                 #  "x_min": int(xmin), "y_min": int(ymin), "x_max": int(xmax), "y_max": int(ymax) })
        #     fake_box = {
        #         "confidence": float(i / 5),
        #         "class_name": f"fake_class_{i}",
        #         "x_min": i * 20,
        #         "y_min": i * 30,
        #         "x_max": (i + 5) * 20,
        #         "y_max": (i + 5) * 30
        #     }
        #     detections.append(fake_box)
            

        # return detections

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
    

