from abc import ABC, abstractmethod
from collections.abc import Sequence, Set
from datetime import date, datetime
from typing import Any, Generic, TypeVar, cast

import msgpack

from .wire_format import (
    AttributeWireType,
    ImmutableMsgPackish,
    RefinedUnknown,
    SetWireType,
    StringWireType,
    Unknown,
    UnrefinedUnknown,
)

# TODO what we really want (but needs HKTVs
#   https://github.com/python/typing/issues/548):
# W = TypeVar("W", bound=AttributeWireType[M])
W = TypeVar("W", bound=AttributeWireType[Any], covariant=True)

# idea inspired by `returns` library HKTs:
# M = TypeVar("M", bound=ImmutableJsonish)
# class AttributeWireTypeTV(Generic[W, M]):
# W_: type[AttributeWireType]
# M_: type[ImmutableJsonish]

T = TypeVar("T")


class AttributeWireTypeUnmarshaler(ABC, Generic[W, T]):
    attribute_wire_type: W

    @abstractmethod
    def unmarshal_msgpack(self, value: ImmutableMsgPackish) -> T:
        pass


class AttributeWireTypeMarshaler(ABC, Generic[W, T]):
    attribute_wire_type: W

    # TODO for an attribute wire type of type W[M], this actually returns M,
    # but there is no way to express that in Python's current typing system
    # (needs generic bounds or HKTVs)
    @abstractmethod
    def marshal_msgpack(self, value: T) -> ImmutableMsgPackish:
        pass


class StringWireTypeUnmarshaler(
    AttributeWireTypeUnmarshaler[StringWireType, str]
):
    attribute_wire_type = StringWireType()

    def unmarshal_msgpack(self, value: ImmutableMsgPackish) -> str:
        if not isinstance(value, str):
            raise TypeError(
                f"expected string but got {value!r} which is of type "
                f"{type(value)}"
            )
        return value


class StringWireTypeMarshaler(AttributeWireTypeMarshaler[StringWireType, str]):
    attribute_wire_type = StringWireType()

    def marshal_msgpack(self, value: Any) -> str:
        if not isinstance(value, str):
            raise TypeError(
                f"expected string but got {value!r} which is of type "
                f"{type(value)}"
            )
        return value


class DateTimeAsStringWireTypeUnmarshaler(
    AttributeWireTypeUnmarshaler[StringWireType, datetime]
):
    attribute_wire_type = StringWireType()

    def unmarshal_msgpack(self, value: ImmutableMsgPackish) -> datetime:
        if not isinstance(value, str):
            raise TypeError(
                f"expected string but got {value!r} which is of type "
                f"{type(value)}"
            )
        return datetime.fromisoformat(value)


class DateTimeAsStringWireTypeMarshaler(
    AttributeWireTypeMarshaler[StringWireType, datetime]
):
    attribute_wire_type = StringWireType()

    def marshal_msgpack(self, value: Any) -> str:
        if not isinstance(value, datetime):
            raise TypeError(
                f"expected datetime but got {value!r} which is of type "
                f"{type(value)}"
            )
        return value.isoformat()


class DateAsStringWireTypeUnmarshaler(
    AttributeWireTypeUnmarshaler[StringWireType, date]
):
    attribute_wire_type = StringWireType()

    def unmarshal_msgpack(self, value: ImmutableMsgPackish) -> date:
        if not isinstance(value, str):
            raise TypeError(
                f"expected string but got {value!r} which is of type "
                f"{type(value)}"
            )
        return date.fromisoformat(value)


class DateAsStringWireTypeMarshaler(
    AttributeWireTypeMarshaler[StringWireType, date]
):
    attribute_wire_type = StringWireType()

    def marshal_msgpack(self, value: Any) -> str:
        if not isinstance(value, date):
            raise TypeError(
                f"expected date but got {value!r} which is of type "
                f"{type(value)}"
            )
        return value.isoformat()


M = TypeVar("M", bound=ImmutableMsgPackish)


class OptionalWireTypeUnmarshaler(
    AttributeWireTypeUnmarshaler[AttributeWireType[M], T | None]
):
    def __init__(
        self, inner: AttributeWireTypeUnmarshaler[AttributeWireType[M], T]
    ):
        self.inner = inner
        self.attribute_wire_type = inner.attribute_wire_type

    def unmarshal_msgpack(self, value: ImmutableMsgPackish) -> T | None:
        return (
            self.inner.unmarshal_msgpack(value) if value is not None else None
        )


class OptionalWireTypeMarshaler(
    AttributeWireTypeMarshaler[AttributeWireType[M], T | None]
):
    def __init__(
        self, inner: AttributeWireTypeMarshaler[AttributeWireType[M], T]
    ):
        self.inner = inner
        self.attribute_wire_type = inner.attribute_wire_type

    def marshal_msgpack(self, value: T | None) -> M | None:
        if value is None:
            return None
        # this type should be correct, but inferring it would require HKTVs
        # that allow us to say attribute_wire_type is of type W[M] and we'd be
        # able to change the method signature of our base class:
        marshaled_value: M = cast(M, self.inner.marshal_msgpack(value))
        return marshaled_value


class MaybeUnknownWireTypeUnmarshaler(
    AttributeWireTypeUnmarshaler[AttributeWireType[M], T | Unknown]
):
    def __init__(
        self, inner: AttributeWireTypeUnmarshaler[AttributeWireType[M], T]
    ):
        self.inner = inner
        self.attribute_wire_type = inner.attribute_wire_type

    def unmarshal_msgpack(self, value: ImmutableMsgPackish) -> T | Unknown:
        if isinstance(value, msgpack.ExtType):
            if value.code == 0:
                return UnrefinedUnknown()
            elif value.code == 12:
                return UnrefinedUnknown()  # TODO actually return refined UK
            else:
                return Unknown()
        else:
            return self.inner.unmarshal_msgpack(value)


class MaybeUnknownWireTypeMarshaler(
    AttributeWireTypeMarshaler[AttributeWireType[M], T | Unknown]
):
    def __init__(
        self, inner: AttributeWireTypeMarshaler[AttributeWireType[M], T]
    ):
        self.inner = inner
        self.attribute_wire_type = inner.attribute_wire_type

    def marshal_msgpack(self, value: T | Unknown) -> M | msgpack.ExtType:
        if isinstance(value, UnrefinedUnknown):
            return msgpack.ExtType(0, b"")
        elif isinstance(value, RefinedUnknown):
            raise msgpack.ExtType(0, b"")  # TODO actually return refined UK
        elif isinstance(value, Unknown):
            assert False, "should never happen (exhaustive)"
        else:
            # this type should be correct, but inferring it would require HKTVs
            # that allow us to say attribute_wire_type is of type W[M] and we'd
            # be able to change the method signature of our base class:
            return cast(M, self.inner.marshal_msgpack(value))


class SetWireTypeUnmarshaler(
    AttributeWireTypeUnmarshaler[AttributeWireType[list[M]], Set[T]]
):
    def __init__(
        self, inner: AttributeWireTypeUnmarshaler[AttributeWireType[M], T]
    ):
        self.inner = inner
        self.attribute_wire_type = SetWireType(inner.attribute_wire_type)

    def unmarshal_msgpack(self, value: ImmutableMsgPackish) -> Set[T]:
        if not isinstance(value, Sequence):
            raise TypeError(f"expected sequence but got {value!r}")
        return set(self.inner.unmarshal_msgpack(elem) for elem in value)


class SetWireTypeMarshaler(
    AttributeWireTypeMarshaler[AttributeWireType[list[M]], Set[T]]
):
    def __init__(
        self, inner: AttributeWireTypeMarshaler[AttributeWireType[M], T]
    ):
        self.inner = inner
        self.attribute_wire_type = SetWireType(inner.attribute_wire_type)

    def marshal_msgpack(self, value: Set[T]) -> list[M]:
        # TODO check if iterable
        # type should be correct, but inferring it would require HKTVs/GBs
        marshaled_value = [self.inner.marshal_msgpack(x) for x in value]
        return cast(list[M], marshaled_value)


#### ye olde #####


# class JsonSerializableWireType(AttributeWireType[F, T]):
# @abstractmethod
# def marshal_value_json(self, value: F) -> ImmutableJsonish:
# pass

# @abstractmethod
# def unmarshal_value_json(self, value: ImmutableJsonish) -> T:
# pass


# class MsgpackSerializableWireType(AttributeWireType[F, T]):
# @abstractmethod
# def marshal_value_msgpack(self, value: F) -> ImmutableMsgPackish:
# pass

# @abstractmethod
# def unmarshal_value_msgpack(self, value: ImmutableMsgPackish) -> T:
# pass


# class JsonAndMsgpackSerializableWireType(
# JsonSerializableWireType[F, T], MsgpackSerializableWireType[F, T]
# ):
# pass


# FIJ = TypeVar("FIJ", bound=ImmutableJsonish)
# TIJ = TypeVar("TIJ", bound=ImmutableJsonish)


# class MarshalJsonish(JsonAndMsgpackSerializableWireType[FIJ, TIJ]):
# def marshal_value_json(self, value: FIJ) -> ImmutableJsonish:
# return value

# def marshal_value_msgpack(self, value: FIJ) -> ImmutableJsonish:
# return value

# # def unmarshal_value_json(self, value: ImmutableJsonish) -> TIJ:
# # return value

# # def unmarshal_value_msgpack(self, value: ImmutableJsonish) -> TIJ:
# # return value


# FJNNP = TypeVar("FJNNP", bound=JsonishNotNonePrimitives)
# TJNNP = TypeVar("TJNNP", bound=JsonishNotNonePrimitives)


# class UnmarshalJsonishNotNonePrimitivesChecked(MarshalJsonish[FJNNP, TJNNP]):
# def unmarshal_value_json(self, value: ImmutableJsonish) -> TJNNP:
# if not isinstance(value, self.to_python_type):
# raise ValueError(
# f"expected a value of type {self.to_python_type}, but got "
# f"{value!r} which is of type {type(value)} instead"
# )
# return value

# def unmarshal_value_msgpack(self, value: ImmutableMsgPackish) -> TJNNP:
# if not isinstance(value, self.to_python_type):
# raise ValueError(
# f"expected a value of type {self.to_python_type}, but got "
# f"{value!r} which is of type {type(value)} instead"
# )
# return value


# class StringWireType(UnmarshalJsonishNotNonePrimitivesChecked[str, str]):
# from_python_type = str
# to_python_type = str

# def marshal_type(self) -> str:
# return "string"


# class NumberWireType(
# UnmarshalJsonishNotNonePrimitivesChecked[
# int | float | str, int | float | str
# ]
# ):
# from_python_type = int | float | str
# to_python_type = int | float | str

# def marshal_type(self) -> ImmutableJsonish:
# return "number"


# class BoolWireType(UnmarshalJsonishNotNonePrimitivesChecked):
# from_python_type = bool
# to_python_type = bool

# def marshal_type(self) -> ImmutableJsonish:
# return "bool"


# W = TypeVar("W", bound=AttributeWireType)
# WJM = TypeVar("WJM", bound=JsonAndMsgpackSerializableWireType)
# WM = TypeVar("WM", bound=MsgpackSerializableWireType)


# class ListWireType(
# JsonAndMsgpackSerializableWireType[list[F], list[T]], Generic[T, F, WJM]
# ):
# def __init__(self, inner_type: WJM):
# self.inner_type = inner_type
# # self.from_python_type = list[inner_type.from_python_type]
# # self.to_python_type = list[inner_type.to_python_type]

# def marshal_type(self) -> ImmutableJsonish:
# return ["list", self.inner_type.marshal_type()]

# def marshal_value_json(self, value: list[F]) -> ImmutableJsonish:
# return [self.inner_type.marshal_value_json(x) for x in value]

# def marshal_value_msgpack(self, value: list[F]) -> ImmutableMsgPackish:
# return [self.inner_type.marshal_value_msgpack(x) for x in value]

# def unmarshal_value_json(self, value: ImmutableJsonish) -> list[T]:
# if not isinstance(value, list):
# raise ValueError(
# f"expected a value of type {self.to_python_type}, but got "
# f"{value!r} which is of type {type(value)} and not even a "
# "list instead"
# )
# return [self.inner_type.unmarshal_value_json(x) for x in value]

# def unmarshal_value_msgpack(self, value: ImmutableMsgPackish) -> list[T]:
# if not isinstance(value, list):
# raise ValueError(
# f"expected a value of type {self.to_python_type}, but got "
# f"{value!r} which is of type {type(value)} and not even a "
# "list instead"
# )
# return [self.inner_type.unmarshal_value_msgpack(x) for x in value]


# class SetWireType(
# JsonAndMsgpackSerializableWireType[set[F], set[T]], Generic[T, F, WJM]
# ):
# def __init__(self, inner_type: WJM):
# self.inner_type = inner_type

# def marshal_type(self) -> ImmutableJsonish:
# return ["set", self.inner_type.marshal_type()]

# def marshal_value_json(self, value: set[F]) -> ImmutableJsonish:
# return [self.inner_type.marshal_value_json(x) for x in value]

# def marshal_value_msgpack(self, value: set[F]) -> ImmutableMsgPackish:
# return [self.inner_type.marshal_value_msgpack(x) for x in value]

# def unmarshal_value_json(self, value: ImmutableJsonish) -> set[T]:
# if not isinstance(value, set):
# raise ValueError(
# f"expected a value of type {self.to_python_type}, but got "
# f"{value!r} which is of type {type(value)} and not even a "
# "set instead"
# )
# return {self.inner_type.unmarshal_value_json(x) for x in value}

# def unmarshal_value_msgpack(self, value: ImmutableMsgPackish) -> set[T]:
# if not isinstance(value, set):
# raise ValueError(
# f"expected a value of type {self.to_python_type}, but got "
# f"{value!r} which is of type {type(value)} and not even a "
# "set instead"
# )
# return {self.inner_type.unmarshal_value_msgpack(x) for x in value}


# class MapWireType(
# JsonAndMsgpackSerializableWireType[dict[str, F], dict[str, T]],
# Generic[T, F, WJM],
# ):
# def __init__(self, inner_type: WJM):
# self.inner_type = inner_type

# def marshal_type(self) -> ImmutableJsonish:
# return ["map", self.inner_type.marshal_type()]

# def marshal_value_json(self, value: dict[str, F]) -> ImmutableJsonish:
# return {
# k: self.inner_type.marshal_value_json(v) for k, v in value.items()
# }

# def marshal_value_msgpack(
# self, value: dict[str, F]
# ) -> ImmutableMsgPackish:
# return {
# k: self.inner_type.marshal_value_msgpack(v)
# for k, v in value.items()
# }

# def unmarshal_value_json(self, value: ImmutableJsonish) -> dict[str, T]:
# if not isinstance(value, dict):
# raise ValueError(
# f"expected a value of type {self.to_python_type}, but got "
# f"{value!r} which is of type {type(value)} and not even a "
# "dict instead"
# )
# return {
# k: self.inner_type.unmarshal_value_json(v)
# for k, v in value.items()
# }

# def unmarshal_value_msgpack(
# self, value: ImmutableMsgPackish
# ) -> dict[str, T]:
# if not isinstance(value, dict):
# raise ValueError(
# f"expected a value of type {self.to_python_type}, but got "
# f"{value!r} which is of type {type(value)} and not even a "
# "dict instead"
# )
# return {
# k: self.inner_type.unmarshal_value_msgpack(v)
# for k, v in value.items()
# }


# class MaybeUnknownWireType(
# JsonAndMsgpackSerializableWireType[F | Unknown, T | Unknown],
# Generic[T, F, WJM],
# ):
# def __init__(self, inner_type: WJM):
# self.inner_type = inner_type

# def marshal_type(self) -> ImmutableJsonish:
# return self.inner_type.marshal_type()

# def marshal_value_json(self, value: F | Unknown) -> ImmutableJsonish:
# # TODO actually change type structure to make this true lol
# raise ValueError(
# "can't represent unknown values in JSON; a type checker "
# "should have made it impossible for this method to be called, "
# "so this is probably a bug"
# )

# def marshal_value_msgpack(self, value: F | Unknown) -> ImmutableMsgPackish:
# if isinstance(value, UnrefinedUnknown):
# return msgpack.ExtType(0, b"")
# elif isinstance(value, RefinedUnknown):
# raise NotImplementedError("")
# elif isinstance(value, Unknown):
# assert False, "should never happen (exhaustive)"
# else:
# return self.inner_type.marshal_value_msgpack(value)

# def unmarshal_value_json(self, value: ImmutableJsonish) -> T | Unknown:
# # TODO actually change type structure to make this true
# raise ValueError(
# "can't represent unknown values in JSON; a type checker "
# "should have made it impossible for this method to be called, "
# "so this is probably a bug"
# )

# def unmarshal_value_msgpack(
# self, value: ImmutableMsgPackish
# ) -> T | Unknown:
# if isinstance(value, msgpack.ExtType):
# if value.code == 0:
# return UnrefinedUnknown()
# elif value.code == 12:
# raise NotImplementedError("")
# else:
# return Unknown()
# else:
# return self.inner_type.unmarshal_value_msgpack(value)


# class RequiredKnownWireType(
# JsonAndMsgpackSerializableWireType[F, T], Generic[T, F, WJM]
# ):
# def __init__(self, inner_type: WJM):
# self.inner_type = inner_type

# def marshal_type(self) -> ImmutableJsonish:
# return self.inner_type.marshal_type()

# def marshal_value_json(self, value: F) -> ImmutableJsonish:
# return self.inner_type.marshal_value_json(value)

# def marshal_value_msgpack(self, value: F) -> ImmutableMsgPackish:
# if isinstance(value, Unknown):
# raise ValueError(
# "got unknown value where only known values were expected"
# )
# else:
# return self.inner_type.marshal_value_msgpack(value)

# def unmarshal_value_json(self, value: ImmutableJsonish) -> T:
# return self.inner_type.unmarshal_value_json(value)

# def unmarshal_value_msgpack(self, value: ImmutableMsgPackish) -> T:
# if isinstance(value, msgpack.ExtType):
# raise ValueError(
# "got unknown value where only known values were expected"
# )
# else:
# return self.inner_type.unmarshal_value_msgpack(value)
