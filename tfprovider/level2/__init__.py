"""
Slightly less low-level API for interacting with Terraform via RPC.

This level introduces decoding of Terraform's "dynamic values"
(bytes-serialized JSON or msgpack) and the type information describing them,
as well as wrappers around some of the raw RPC datatypes to both allow
typechecking and deal with the higher-level representations of dynamic value
types.
"""
