import asyncio
from sys import stderr

from tfprovider.level2.diagnostics import Diagnostics
from tfprovider.level3.statically_typed_schema import attribute, attributes_class
from tfprovider.level4.async_provider_servicer import Provider as BaseProvider
from tfprovider.level4.async_provider_servicer import Resource as BaseResource


@attributes_class()
class HelloWorldCompleteProviderConfig:
    foo: str = attribute(required=True)


@attributes_class()
class HelloWorldCompleteResConfig:
    foo: str = attribute(required=True)
    # bar: datetime = attribute(representation=DateAsStringRepr())


class HelloWorldResResource(BaseResource):
    type_name = "helloworld_res"
    config_type = HelloWorldCompleteResConfig

    schema_version = 1
    block_version = 1

    async def validate_resource_config(
        self, config: HelloWorldCompleteResConfig, diagnostics: Diagnostics
    ) -> None:
        print(f"vrc {config.foo=}", file=stderr)

    async def plan_resource_change(
        self,
        prior_state: HelloWorldCompleteResConfig | None,
        config: HelloWorldCompleteResConfig,
        proposed_new_state: HelloWorldCompleteResConfig | None,
        diagnostics: Diagnostics,
    ) -> HelloWorldCompleteResConfig:
        print(f"prc {config.foo=}", file=stderr)
        assert proposed_new_state is not None
        return proposed_new_state

    async def apply_resource_change(
        self,
        prior_state: HelloWorldCompleteResConfig | None,
        config: HelloWorldCompleteResConfig | None,
        proposed_new_state: HelloWorldCompleteResConfig | None,
        diagnostics: Diagnostics,
    ) -> HelloWorldCompleteResConfig | None:
        if config is not None:
            print(f"arc {config.foo=}", file=stderr)
        else:
            print("DESTROY", file=stderr)
        return proposed_new_state

    async def upgrade_resource_state(
        self,
        state: HelloWorldCompleteResConfig,
        version: int,
        diagnostics: Diagnostics,
    ) -> HelloWorldCompleteResConfig:
        return state

    async def read_resource(
        self, current_state: HelloWorldCompleteResConfig, diagnostics: Diagnostics
    ) -> HelloWorldCompleteResConfig:
        return current_state

    async def import_resource(
        self, id: str, diagnostics: Diagnostics) -> HelloWorldCompleteResConfig:
        raise NotImplementedError("resource imports not yet implemented")


class Provider(BaseProvider):
    provider_state = None
    resource_factories = [HelloWorldResResource]
    config_type = HelloWorldCompleteProviderConfig

    schema_version = 1
    block_version = 1

    async def validate_provider_config(
        self, config: HelloWorldCompleteProviderConfig, diagnostics: Diagnostics
    ) -> None:
        print(f"vpc {config.foo=}", file=stderr)


def main() -> None:
    s = Provider()
    asyncio.run(s.run())


if __name__ == "__main__":
    main()
