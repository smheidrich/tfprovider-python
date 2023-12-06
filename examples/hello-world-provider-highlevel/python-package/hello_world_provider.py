from sys import stderr
from typing import Any

from tfprovider.level1.rpc_plugin import RPCPluginServer
from tfprovider.level2.usable_schema import Block, ProviderSchema, Schema, StringKind
from tfprovider.level3.statically_typed_schema import (
    attribute,
    attributes_class,
    attributes_class_to_usable,
)
from tfprovider.level4.provider_servicer import ProviderResource as BaseProviderResource
from tfprovider.level4.provider_servicer import ProviderServicer as BaseProviderServicer


@attributes_class()
class HelloWorldCompleteProviderConfig:
    foo: str = attribute(required=True)


@attributes_class()
class HelloWorldCompleteResConfig:
    foo: str = attribute(required=True)
    # bar: datetime = attribute(representation=DateAsStringRepr())


provider_schema = ProviderSchema(
    provider=Schema(
        version=1,
        block=Block(
            version=1,
            attributes=attributes_class_to_usable(HelloWorldCompleteProviderConfig),
        ),
    ),
    resource_schemas={
        "helloworld_res": Schema(
            version=1,
            block=Block(
                version=1,
                description="Some resource",
                description_kind=StringKind.PLAIN,
                attributes=attributes_class_to_usable(HelloWorldCompleteResConfig),
            ),
        )
    },
)


class HelloWorldResResource(BaseProviderResource):
    type_name = "helloworld_res"
    config_type = HelloWorldCompleteResConfig

    def validate_resource_config(
        self, config: HelloWorldCompleteResConfig, diagnostics
    ) -> None:
        print(f"vrc {config.foo=}", file=stderr)

    def plan_resource_change(
        self, config: HelloWorldCompleteResConfig, diagnostics: Any
    ) -> HelloWorldCompleteResConfig:
        print(f"prc {config.foo=}", file=stderr)
        return config


class ProviderServicer(BaseProviderServicer):
    provider_state = None
    provider_schema = provider_schema
    resource_factories = [HelloWorldResResource]
    config_type = HelloWorldCompleteProviderConfig

    def validate_provider_config(
        self, config: HelloWorldCompleteProviderConfig, diagnostics
    ) -> None:
        print(f"vpc {config.foo=}", file=stderr)


def main():
    s = RPCPluginServer(ProviderServicer().adapt())
    s.run()


if __name__ == "__main__":
    main()
