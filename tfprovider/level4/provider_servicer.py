from abc import ABC
from typing import Any, Generic, TypeVar

from ..level1.tfplugin64_pb2 import (
    ConfigureProvider,
    GetMetadata,
    PlanResourceChange,
    ServerCapabilities,
    ValidateProviderConfig,
    ValidateResourceConfig,
)
from ..level1.tfplugin64_pb2_grpc import (
    ProviderServicer as L1BaseProviderServicer,
)
from ..level2.usable_schema import ProviderSchema
from ..level3.statically_typed_schema import (
    deserialize_dynamic_value_into_attribute_class_instance,
    serialize_attribute_class_instance_to_dynamic_value,
)


class AdapterProviderServicer(L1BaseProviderServicer):
    adapted: "ProviderServicer"

    def __init__(self, adapted: "ProviderServicer"):
        self.adapted = adapted

    def GetMetadata(self, request, context):
        self.adapted.init()
        return GetMetadata.Response(
            server_capabilities=ServerCapabilities(
                plan_destroy=False, get_provider_schema_optional=False
            ),
        )

    def GetProviderSchema(self, request, context):
        # TODO also init() here if getmetadata wasnt called
        return self.adapted.provider_schema.to_protobuf()

    def ValidateProviderConfig(self, request, context):
        config = deserialize_dynamic_value_into_attribute_class_instance(
            request.config, self.adapted.config_type
        )
        # TODO diag
        self.adapted.validate_provider_config(config, None)
        return ValidateProviderConfig.Response()

    def ValidateResourceConfig(self, request, context):
        resource = self._get_resource_by_name(request.type_name)
        config = deserialize_dynamic_value_into_attribute_class_instance(
            request.config, resource.config_type
        )
        resource.validate_resource_config(config, None)  # TODO diag
        return ValidateResourceConfig.Response()

    def ConfigureProvider(self, request, context):
        config = deserialize_dynamic_value_into_attribute_class_instance(
            request.config, self.adapted.config_type
        )
        # TODO diag
        self.adapted.configure_provider(config, None)
        return ConfigureProvider.Response()

    def PlanResourceChange(self, request, context):
        resource = self._get_resource_by_name(request.type_name)
        config = deserialize_dynamic_value_into_attribute_class_instance(
            request.config, resource.config_type
        )
        # TODO prior + proposed new + private + diag
        planned_state = resource.plan_resource_change(config, None)
        serialized_planned_state = (
            serialize_attribute_class_instance_to_dynamic_value(planned_state)
        )
        return PlanResourceChange.Response(
            planned_state=serialized_planned_state
        )

    def _get_resource_by_name(self, type_name: str) -> "ProviderResource":
        resource = self.adapted.resources[type_name]
        return resource


PS = TypeVar("PS")  # ProviderState
PC = TypeVar("PC")  # ProviderConfig
RC = TypeVar("RC")  # ResourceConfig


class ProviderServicer(ABC, Generic[PS, PC, RC]):
    provider_state: PS
    "*Must* be overridden by subclasses."
    # TODO should not be L2 schema but a new one: ProviderSchema[PC]
    schema: ProviderSchema
    "*Must* be overridden by subclasses."
    resource_factories: list[type["ProviderResource[PS, RC]"]]
    "*Must* be overridden by subclasses."
    config_type: type[PC]

    resources: dict[str, "ProviderResource[PS, RC]"]

    def __init__(self) -> None:
        self.resources = {
            rf.type_name: rf(self.provider_state)
            for rf in self.resource_factories
        }

    # TODO unclear if this is a good approach...
    def adapt(self) -> AdapterProviderServicer:
        return AdapterProviderServicer(self)

    def init(self, diagnostics: Any) -> None:  # TODO type of diag?
        """
        To be overridden by subclasses if needed.
        """

    def validate_provider_config(self, config: PC, diagnostics: Any) -> None:
        """
        To be overridden by subclasses if needed.
        """

    def configure_provider(self, config: PC, diagnostics: Any) -> None:
        """
        To be overridden by subclasses if needed.
        """


class ProviderResource(ABC, Generic[PS, RC]):
    type_name: str
    "*Must* be overridden by subclasses."
    config_type: type[RC]
    "*Must* be overridden by subclasses."

    provider_state: PS

    def __init__(self, provider_state: PS) -> None:
        self.provider_state = provider_state

    def validate_resource_config(self, config: RC, diagnostics: Any) -> None:
        """
        To be overridden by subclasses if needed.
        """

    def plan_resource_change(self, config: RC, diagnostics: Any) -> RC:
        """
        To be overridden by subclasses if needed.
        """
        return config