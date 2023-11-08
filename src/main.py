import asyncio

from viam.services.vision import Vision
from viam.module.module import Module
from viam.resource.registry import Registry, ResourceCreatorRegistration
from directai_beta.directai_beta import DirectModel


async def main():
    """
    This function creates and starts a new module, after adding all desired
    resource models. Resource creators must be registered to the resource
    registry before the module adds the resource model.
    """
    Registry.register_resource_creator(
        Vision.SUBTYPE,
        DirectModel.MODEL,
        ResourceCreatorRegistration(DirectModel.new_service, DirectModel.validate_config))
    module = Module.from_args()

    module.add_model_from_registry(Vision.SUBTYPE, DirectModel.MODEL)
    print(Vision.SUBTYPE, DirectModel.MODEL)
    # 1/0
    await module.start()
    await module.cleanup()


if __name__ == "__main__":
    asyncio.run(main())