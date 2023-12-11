from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from ..level1.rpc_plugin import AsyncRPCPluginServer
from ..level1.tfplugin64_pb2 import (
    ApplyResourceChange,
    ConfigureProvider,
    GetMetadata,
    PlanResourceChange,
    ReadResource,
    ServerCapabilities,
    UpgradeResourceState,
    ValidateProviderConfig,
    ValidateResourceConfig,
)
from ..level1.tfplugin64_pb2_grpc import (
    ProviderServicer as L1BaseProviderServicer,
)
from ..level2.diagnostics import Diagnostics
from ..level2.usable_schema import (
    NOT_SET,
    Block,
    NotSet,
    ProviderSchema,
    Schema,
    StringKind,
)
from ..level3.statically_typed_schema import (
    attributes_class_to_usable,
    deserialize_dynamic_value_into_attribute_class_instance,
    deserialize_dynamic_value_into_optional_attribute_class_instance,
    deserialize_raw_state_into_optional_attribute_class_instance,
    serialize_attribute_class_instance_to_dynamic_value,
    serialize_optional_attribute_class_instance_to_dynamic_value,
)
from .provider_servicer import exception_to_diagnostics

# TODO refactor: DRY w/r/t sync variant


class AdapterProviderServicer(L1BaseProviderServicer):
    adapted: "Provider"

    def __init__(self, adapted: "Provider"):
        self.adapted = adapted

    async def GetMetadata(self, request, context):
        await self.adapted.init()
        return GetMetadata.Response(
            server_capabilities=ServerCapabilities(
                plan_destroy=False, get_provider_schema_optional=False
            ),
        )

    async def GetProviderSchema(self, request, context):
        # TODO also init() here if getmetadata wasnt called
        return self.adapted.provider_schema.to_protobuf()

    async def ValidateProviderConfig(self, request, context):
        diagnostics = Diagnostics()
        with exception_to_diagnostics(diagnostics):
            config = deserialize_dynamic_value_into_attribute_class_instance(
                request.config, self.adapted.config_type
            )
            await self.adapted.validate_provider_config(config, diagnostics)
        return ValidateProviderConfig.Response(diagnostics=diagnostics)

    async def ValidateResourceConfig(self, request, context):
        diagnostics = Diagnostics()
        with exception_to_diagnostics(diagnostics):
            resource = self._get_resource_by_name(request.type_name)
            config = deserialize_dynamic_value_into_attribute_class_instance(
                request.config, resource.config_type
            )
            await resource.validate_resource_config(config, diagnostics)
        return ValidateResourceConfig.Response(diagnostics=diagnostics)

    async def ConfigureProvider(self, request, context):
        diagnostics = Diagnostics()
        with exception_to_diagnostics(diagnostics):
            config = deserialize_dynamic_value_into_attribute_class_instance(
                request.config, self.adapted.config_type
            )
            await self.adapted.configure_provider(config, diagnostics)
        return ConfigureProvider.Response(diagnostics=diagnostics)

    async def PlanResourceChange(self, request, context):
        diagnostics = Diagnostics()
        with exception_to_diagnostics(diagnostics):
            resource = self._get_resource_by_name(request.type_name)
            prior_state = deserialize_dynamic_value_into_optional_attribute_class_instance(
                request.prior_state, resource.config_type
            )
            config = deserialize_dynamic_value_into_attribute_class_instance(
                request.config, resource.config_type
            )
            proposed_new_state = deserialize_dynamic_value_into_optional_attribute_class_instance(
                request.proposed_new_state, resource.config_type
            )
            # TODO private + requires replace + provider meta
            planned_state = await resource.plan_resource_change(
                prior_state, config, proposed_new_state, diagnostics
            )
            serialized_planned_state = (
                serialize_attribute_class_instance_to_dynamic_value(
                    planned_state
                )
            )
            return PlanResourceChange.Response(
                planned_state=serialized_planned_state, diagnostics=diagnostics
            )
        return PlanResourceChange.Response(diagnostics=diagnostics)

    async def ApplyResourceChange(self, request, context):
        diagnostics = Diagnostics()
        with exception_to_diagnostics(diagnostics):
            resource = self._get_resource_by_name(request.type_name)
            prior_state = deserialize_dynamic_value_into_optional_attribute_class_instance(
                request.prior_state, resource.config_type
            )
            config = deserialize_dynamic_value_into_optional_attribute_class_instance(
                request.config, resource.config_type
            )
            planned_state = deserialize_dynamic_value_into_optional_attribute_class_instance(
                request.planned_state, resource.config_type
            )
            # TODO private + requires replace + provider meta
            new_state = await resource.apply_resource_change(
                prior_state, config, planned_state, diagnostics
            )
            serialized_new_state = (
                serialize_optional_attribute_class_instance_to_dynamic_value(
                    new_state
                )
            )
            return ApplyResourceChange.Response(
                new_state=serialized_new_state, diagnostics=diagnostics
            )
        return ApplyResourceChange.Response(diagnostics=diagnostics)

    async def UpgradeResourceState(self, request, context):
        diagnostics = Diagnostics()
        with exception_to_diagnostics(diagnostics):
            resource = self._get_resource_by_name(request.type_name)
            state = (
                deserialize_raw_state_into_optional_attribute_class_instance(
                    request.raw_state, resource.config_type
                )
            )
            upgraded_state = await resource.upgrade_resource_state(
                state, request.version, diagnostics
            )
            serialized_upgraded_state = (
                serialize_attribute_class_instance_to_dynamic_value(
                    upgraded_state
                )
            )
            return UpgradeResourceState.Response(
                upgraded_state=serialized_upgraded_state,
                diagnostics=diagnostics,
            )
        return UpgradeResourceState.Response(diagnostics=diagnostics)

    async def ReadResource(self, request, context):
        diagnostics = Diagnostics()
        with exception_to_diagnostics(diagnostics):
            resource = self._get_resource_by_name(request.type_name)
            current_state = (
                deserialize_dynamic_value_into_attribute_class_instance(
                    request.current_state, resource.config_type
                )
            )
            # TODO private + provider meta
            new_state = await resource.read_resource(
                current_state, diagnostics
            )
            serialized_new_state = (
                serialize_attribute_class_instance_to_dynamic_value(new_state)
            )
            return ReadResource.Response(
                new_state=serialized_new_state,
                diagnostics=diagnostics,
            )
        return ReadResource.Response(diagnostics=diagnostics)

    def _get_resource_by_name(self, type_name: str) -> "Resource":
        resource = self.adapted.resources[type_name]
        return resource


C = TypeVar("C")  # Provider or Resource config
PS = TypeVar("PS")  # ProviderState
PC = TypeVar("PC")  # ProviderConfig
RC = TypeVar("RC")  # ResourceConfig


class DefinesSchema(Generic[C]):
    """
    Mixin for Terraform schema defining classes (= providers and resources).
    """

    config_type: type[C]
    "*Must* be overridden by subclasses."

    # Stuff that goes directly into generating the corresponding TF Schema:
    schema_version: int
    "*Must* be overridden by subclasses."
    block_version: int
    "*Must* be overridden by subclasses."
    description: str | NotSet = NOT_SET  # TODO extract from docstring
    "May be overridden by base classes"
    description_kind: StringKind | NotSet = NOT_SET
    "May be overridden by base classes"

    @property
    def schema(self) -> Schema:
        return Schema(
            version=self.schema_version,
            block=Block(
                version=self.block_version,
                description=self.description,
                description_kind=self.description_kind,
                attributes=attributes_class_to_usable(self.config_type),
            ),
        )


class Provider(DefinesSchema[PC], ABC, Generic[PS, PC, RC]):
    provider_state: PS
    "*Must* be overridden by subclasses."

    resource_factories: list[type["Resource[PS, RC]"]]
    "*Must* be overridden by subclasses."

    # quasi internal state
    resources: dict[str, "Resource[PS, RC]"]

    def __init__(self) -> None:
        self.resources = {
            rf.type_name: rf(self.provider_state)
            for rf in self.resource_factories
        }

    # TODO unclear if this is a good approach...
    def adapt(self) -> AdapterProviderServicer:
        return AdapterProviderServicer(self)

    async def init(self, diagnostics: Diagnostics) -> None:
        """
        To be overridden by subclasses if needed.
        """

    async def validate_provider_config(
        self, config: PC, diagnostics: Diagnostics
    ) -> None:
        """
        To be overridden by subclasses if needed.
        """

    async def configure_provider(
        self, config: PC, diagnostics: Diagnostics
    ) -> None:
        """
        To be overridden by subclasses if needed.
        """

    # automatically provided, not generally necessary to be overridden:

    # TODO should not be L2 schema but a new one: ProviderSchema[PC]
    @property
    def provider_schema(self) -> ProviderSchema:
        return ProviderSchema(
            provider=self.schema,
            resource_schemas={
                res_name: res.schema
                for res_name, res in self.resources.items()
            },
        )

    # TODO not yet sure whether this is a good idea...
    async def run(self) -> None:
        s = AsyncRPCPluginServer(self.adapt())
        await s.run()


class Resource(DefinesSchema[RC], ABC, Generic[PS, RC]):
    type_name: str
    "*Must* be overridden by subclasses."

    # internal shared state
    provider_state: PS

    def __init__(self, provider_state: PS) -> None:
        self.provider_state = provider_state

    def validate_resource_config(
        self, config: RC, diagnostics: Diagnostics
    ) -> None:
        """
        To be overridden by subclasses if needed.
        """

    def plan_resource_change(
        self,
        prior_state: RC | None,
        config: RC,
        proposed_new_state: RC | None,
        diagnostics: Diagnostics,
    ) -> RC:
        """
        To be overridden by subclasses if needed.
        """
        return config

    @abstractmethod
    def apply_resource_change(
        self,
        prior_state: RC | None,
        config: RC | None,
        proposed_new_state: RC | None,
        diagnostics: Diagnostics,
    ) -> RC | None:
        """
        To be overridden by subclasses.
        """

    # TODO considering this is meant to upgrade state from prev. versions, it
    #   probably doesn't make sense to have the same RC type here as for the
    #   other methods... => introduce ORC (old resource config) type (w/
    #   possibility of making it a union)? or just pass the JSON?
    @abstractmethod
    def upgrade_resource_state(
        self, state: RC, version: int, diagnostics: Diagnostics
    ) -> RC:
        """
        To be overridden by subclasses.
        """

    @abstractmethod
    def read_resource(self, current_state: RC, diagnostics: Diagnostics) -> RC:
        """
        To be overridden by subclasses.
        """
