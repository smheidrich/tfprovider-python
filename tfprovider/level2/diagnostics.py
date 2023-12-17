from collections import UserList
from collections.abc import Sequence
from typing import Union

from tfplugin_proto.tfplugin6_4_pb2 import AttributePath, Diagnostic
from .usable_schema import NOT_SET, NotSet


class Diagnostics(UserList[Diagnostic]):
    def add_error(
        self,
        summary: str | NotSet = NOT_SET,
        detail: str | NotSet = NOT_SET,
        attribute: AttributePath | NotSet = NOT_SET,
    ) -> None:
        self.add_diagnostic(
            severity=Diagnostic.Severity.ERROR,
            summary=summary,
            detail=detail,
            attribute=attribute,
        )

    def add_warning(
        self,
        summary: str | NotSet = NOT_SET,
        detail: str | NotSet = NOT_SET,
        attribute: AttributePath | NotSet = NOT_SET,
    ) -> None:
        self.add_diagnostic(
            severity=Diagnostic.Severity.WARNING,
            summary=summary,
            detail=detail,
            attribute=attribute,
        )

    def add_diagnostic(
        self,
        severity: Union[Diagnostic.Severity, NotSet] = NOT_SET,
        summary: str | NotSet = NOT_SET,
        detail: str | NotSet = NOT_SET,
        attribute: AttributePath | NotSet = NOT_SET,
    ) -> None:
        d = {
            k: v
            for k, v in {
                "summary": summary,
                "detail": detail,
                "attribute": attribute,
            }.items()
            if v != NOT_SET
        }
        self.append(Diagnostic(severity=severity, **d))  # type: ignore

    def errors(self) -> Sequence[Diagnostic]:
        return [x for x in self if x.severity == Diagnostic.Severity.ERROR]

    def warnings(self) -> Sequence[Diagnostic]:
        return [x for x in self if x.severity == Diagnostic.Severity.ERROR]

    def to_protobuf(self) -> list[Diagnostic]:
        return list(self)
