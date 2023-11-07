"""
Terraform "object wire format", as documented in:
https://github.com/hashicorp/terraform/blob/bdc38b6527ee9927cee67cc992e02cc199f3cae1/docs/plugin-protocol/object-wire-format.md
"""
import json
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Generic, TypeAlias, TypeVar

import msgpack


@dataclass
class Unknown:
    pass


@dataclass
class UnrefinedUnknown(Unknown):
    pass


@dataclass
class RefinedUnknown(Unknown):
    pass


JsonishNotNonePrimitives: TypeAlias = str | int | float | bool

JsonishPrimitives: TypeAlias = JsonishNotNonePrimitives | None

ImmutableJsonish: TypeAlias = (
    Mapping[str, "ImmutableJsonish"]
    | Sequence["ImmutableJsonish"]
    | JsonishPrimitives
)

ImmutableJsonishWithUnknown: TypeAlias = (
    Mapping[str, "ImmutableJsonishWithUnknown"]
    | Sequence["ImmutableJsonishWithUnknown"]
    | JsonishPrimitives
    | Unknown
)

ImmutableMsgPackish: TypeAlias = (
    Mapping[str, "ImmutableMsgPackish"]
    | Sequence["ImmutableMsgPackish"]
    | JsonishPrimitives
    | msgpack.ExtType
)

F = TypeVar("F")
T = TypeVar("T")

# types


class WireType(ABC, Generic[F, T]):
    from_python_type: type[F]
    to_python_type: type[T]

    def serialize_type(self) -> bytes:
        return json.dumps(self.marshal_type()).encode("utf-8")

    @abstractmethod
    def marshal_type(self) -> ImmutableJsonish:
        pass


class JsonSerializableWireType(WireType[F, T]):
    @abstractmethod
    def marshal_value_json(self, value: F) -> ImmutableJsonish:
        pass

    @abstractmethod
    def unmarshal_value_json(self, value: ImmutableJsonish) -> T:
        pass


class MsgpackSerializableWireType(WireType[F, T]):
    @abstractmethod
    def marshal_value_msgpack(self, value: F) -> ImmutableMsgPackish:
        pass

    @abstractmethod
    def unmarshal_value_msgpack(self, value: ImmutableMsgPackish) -> T:
        pass


class JsonAndMsgpackSerializableWireType(
    JsonSerializableWireType[F, T], MsgpackSerializableWireType[F, T]
):
    pass


FIJ = TypeVar("FIJ", bound=ImmutableJsonish)
TIJ = TypeVar("TIJ", bound=ImmutableJsonish)


class MarshalJsonish(JsonAndMsgpackSerializableWireType[FIJ, TIJ]):
    def marshal_value_json(self, value: FIJ) -> ImmutableJsonish:
        return value

    def marshal_value_msgpack(self, value: FIJ) -> ImmutableJsonish:
        return value

    # def unmarshal_value_json(self, value: ImmutableJsonish) -> TIJ:
    # return value

    # def unmarshal_value_msgpack(self, value: ImmutableJsonish) -> TIJ:
    # return value


FJNNP = TypeVar("FJNNP", bound=JsonishNotNonePrimitives)
TJNNP = TypeVar("TJNNP", bound=JsonishNotNonePrimitives)


class UnmarshalJsonishNotNonePrimitivesChecked(MarshalJsonish[FJNNP, TJNNP]):
    def unmarshal_value_json(self, value: ImmutableJsonish) -> TJNNP:
        if not isinstance(value, self.to_python_type):
            raise ValueError(
                f"expected a value of type {self.to_python_type}, but got "
                f"{value!r} which is of type {type(value)} instead"
            )
        return value

    def unmarshal_value_msgpack(self, value: ImmutableMsgPackish) -> TJNNP:
        if not isinstance(value, self.to_python_type):
            raise ValueError(
                f"expected a value of type {self.to_python_type}, but got "
                f"{value!r} which is of type {type(value)} instead"
            )
        return value


class StringWireType(UnmarshalJsonishNotNonePrimitivesChecked[str, str]):
    from_python_type = str
    to_python_type = str

    def marshal_type(self) -> str:
        return "string"


class NumberWireType(
    UnmarshalJsonishNotNonePrimitivesChecked[
        int | float | str, int | float | str
    ]
):
    from_python_type = int | float | str
    to_python_type = int | float | str

    def marshal_type(self) -> ImmutableJsonish:
        return "number"


class BoolWireType(UnmarshalJsonishNotNonePrimitivesChecked):
    from_python_type = bool
    to_python_type = bool

    def marshal_type(self) -> ImmutableJsonish:
        return "bool"


W = TypeVar("W", bound=WireType)
WJM = TypeVar("WJM", bound=JsonAndMsgpackSerializableWireType)
WM = TypeVar("WM", bound=MsgpackSerializableWireType)


class ListWireType(
    JsonAndMsgpackSerializableWireType[list[F], list[T]], Generic[T, F, WJM]
):
    def __init__(self, inner_type: WJM):
        self.inner_type = inner_type
        # self.from_python_type = list[inner_type.from_python_type]
        # self.to_python_type = list[inner_type.to_python_type]

    def marshal_type(self) -> ImmutableJsonish:
        return ["list", self.inner_type.marshal_type()]

    def marshal_value_json(self, value: list[F]) -> ImmutableJsonish:
        return [self.inner_type.marshal_value_json(x) for x in value]

    def marshal_value_msgpack(self, value: list[F]) -> ImmutableMsgPackish:
        return [self.inner_type.marshal_value_msgpack(x) for x in value]

    def unmarshal_value_json(self, value: ImmutableJsonish) -> list[T]:
        if not isinstance(value, list):
            raise ValueError(
                f"expected a value of type {self.to_python_type}, but got "
                f"{value!r} which is of type {type(value)} and not even a "
                "list instead"
            )
        return [self.inner_type.unmarshal_value_json(x) for x in value]

    def unmarshal_value_msgpack(self, value: ImmutableMsgPackish) -> list[T]:
        if not isinstance(value, list):
            raise ValueError(
                f"expected a value of type {self.to_python_type}, but got "
                f"{value!r} which is of type {type(value)} and not even a "
                "list instead"
            )
        return [self.inner_type.unmarshal_value_msgpack(x) for x in value]


class SetWireType(
    JsonAndMsgpackSerializableWireType[set[F], set[T]], Generic[T, F, WJM]
):
    def __init__(self, inner_type: WJM):
        self.inner_type = inner_type

    def marshal_type(self) -> ImmutableJsonish:
        return ["set", self.inner_type.marshal_type()]

    def marshal_value_json(self, value: set[F]) -> ImmutableJsonish:
        return [self.inner_type.marshal_value_json(x) for x in value]

    def marshal_value_msgpack(self, value: set[F]) -> ImmutableMsgPackish:
        return [self.inner_type.marshal_value_msgpack(x) for x in value]

    def unmarshal_value_json(self, value: ImmutableJsonish) -> set[T]:
        if not isinstance(value, set):
            raise ValueError(
                f"expected a value of type {self.to_python_type}, but got "
                f"{value!r} which is of type {type(value)} and not even a "
                "set instead"
            )
        return {self.inner_type.unmarshal_value_json(x) for x in value}

    def unmarshal_value_msgpack(self, value: ImmutableMsgPackish) -> set[T]:
        if not isinstance(value, set):
            raise ValueError(
                f"expected a value of type {self.to_python_type}, but got "
                f"{value!r} which is of type {type(value)} and not even a "
                "set instead"
            )
        return {self.inner_type.unmarshal_value_msgpack(x) for x in value}


class MapWireType(
    JsonAndMsgpackSerializableWireType[dict[str, F], dict[str, T]],
    Generic[T, F, WJM],
):
    def __init__(self, inner_type: WJM):
        self.inner_type = inner_type

    def marshal_type(self) -> ImmutableJsonish:
        return ["map", self.inner_type.marshal_type()]

    def marshal_value_json(self, value: dict[str, F]) -> ImmutableJsonish:
        return {
            k: self.inner_type.marshal_value_json(v) for k, v in value.items()
        }

    def marshal_value_msgpack(
        self, value: dict[str, F]
    ) -> ImmutableMsgPackish:
        return {
            k: self.inner_type.marshal_value_msgpack(v)
            for k, v in value.items()
        }

    def unmarshal_value_json(self, value: ImmutableJsonish) -> dict[str, T]:
        if not isinstance(value, dict):
            raise ValueError(
                f"expected a value of type {self.to_python_type}, but got "
                f"{value!r} which is of type {type(value)} and not even a "
                "dict instead"
            )
        return {
            k: self.inner_type.unmarshal_value_json(v)
            for k, v in value.items()
        }

    def unmarshal_value_msgpack(
        self, value: ImmutableMsgPackish
    ) -> dict[str, T]:
        if not isinstance(value, dict):
            raise ValueError(
                f"expected a value of type {self.to_python_type}, but got "
                f"{value!r} which is of type {type(value)} and not even a "
                "dict instead"
            )
        return {
            k: self.inner_type.unmarshal_value_msgpack(v)
            for k, v in value.items()
        }


class MaybeUnknownWireType(
    JsonAndMsgpackSerializableWireType[F | Unknown, T | Unknown],
    Generic[T, F, WJM],
):
    def __init__(self, inner_type: WJM):
        self.inner_type = inner_type

    def marshal_type(self) -> ImmutableJsonish:
        return self.inner_type.marshal_type()

    def marshal_value_json(self, value: F | Unknown) -> ImmutableJsonish:
        # TODO actually change type structure to make this true lol
        raise ValueError(
            "can't represent unknown values in JSON; a type checker "
            "should have made it impossible for this method to be called, "
            "so this is probably a bug"
        )

    def marshal_value_msgpack(self, value: F | Unknown) -> ImmutableMsgPackish:
        if isinstance(value, UnrefinedUnknown):
            return msgpack.ExtType(0, b"")
        elif isinstance(value, RefinedUnknown):
            raise NotImplementedError("")
        elif isinstance(value, Unknown):
            assert False, "should never happen (exhaustive)"
        else:
            return self.inner_type.marshal_value_msgpack(value)

    def unmarshal_value_json(self, value: ImmutableJsonish) -> T | Unknown:
        # TODO actually change type structure to make this true
        raise ValueError(
            "can't represent unknown values in JSON; a type checker "
            "should have made it impossible for this method to be called, "
            "so this is probably a bug"
        )

    def unmarshal_value_msgpack(
        self, value: ImmutableMsgPackish
    ) -> T | Unknown:
        if isinstance(value, msgpack.ExtType):
            if value.code == 0:
                return UnrefinedUnknown()
            elif value.code == 12:
                raise NotImplementedError("")
            else:
                return Unknown()
        else:
            return self.inner_type.unmarshal_value_msgpack(value)


class RequiredKnownWireType(
    JsonAndMsgpackSerializableWireType[F, T], Generic[T, F, WJM]
):
    def __init__(self, inner_type: WJM):
        self.inner_type = inner_type

    def marshal_type(self) -> ImmutableJsonish:
        return self.inner_type.marshal_type()

    def marshal_value_json(self, value: F) -> ImmutableJsonish:
        return self.inner_type.marshal_value_json(value)

    def marshal_value_msgpack(self, value: F) -> ImmutableMsgPackish:
        if isinstance(value, Unknown):
            raise ValueError(
                "got unknown value where only known values were expected"
            )
        else:
            return self.inner_type.marshal_value_msgpack(value)

    def unmarshal_value_json(self, value: ImmutableJsonish) -> T:
        return self.inner_type.unmarshal_value_json(value)

    def unmarshal_value_msgpack(self, value: ImmutableMsgPackish) -> T:
        if isinstance(value, msgpack.ExtType):
            raise ValueError(
                "got unknown value where only known values were expected"
            )
        else:
            return self.inner_type.unmarshal_value_msgpack(value)
