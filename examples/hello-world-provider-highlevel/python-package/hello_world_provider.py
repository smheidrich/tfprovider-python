from sys import stderr
from typing import Any

from tfprovider.level3.statically_typed_schema import attribute, attributes_class
from tfprovider.level4.provider_servicer import ProviderResource as BaseProviderResource
from tfprovider.level4.provider_servicer import ProviderServicer as BaseProviderServicer


@attributes_class()
class HelloWorldCompleteProviderConfig:
    foo: str = attribute(required=True)


@attributes_class()
class HelloWorldCompleteResConfig:
    foo: str = attribute(required=True)
    # bar: datetime = attribute(representation=DateAsStringRepr())


class HelloWorldResResource(BaseProviderResource):
    type_name = "helloworld_res"
    config_type = HelloWorldCompleteResConfig

    schema_version = 1
    block_version = 1

    def validate_resource_config(
        self, config: HelloWorldCompleteResConfig, diagnostics
    ) -> None:
        print(f"vrc {config.foo=}", file=stderr)

    def plan_resource_change(
        self,
        prior_state: HelloWorldCompleteResConfig | None,
        config: HelloWorldCompleteResConfig,
        proposed_new_state: HelloWorldCompleteResConfig | None,
        diagnostics: Any,
    ) -> HelloWorldCompleteResConfig:
        print(f"prc {config.foo=}", file=stderr)
        return config


class ProviderServicer(BaseProviderServicer):
    provider_state = None
    resource_factories = [HelloWorldResResource]
    config_type = HelloWorldCompleteProviderConfig

    schema_version = 1
    block_version = 1

    def validate_provider_config(
        self, config: HelloWorldCompleteProviderConfig, diagnostics
    ) -> None:
        print(f"vpc {config.foo=}", file=stderr)


def main():
    s = ProviderServicer()
    s.run()


if __name__ == "__main__":
    main()
