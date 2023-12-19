"""
Lowest-level API for interacting with Terraform via RPC.

Exposes the RPC data types directly without any transformations to e.g. decode
binary data contained therein, let alone to make the interface more Pythonic.

At this point, this is just a thin layer around a separate go-plugin/RPCPlugin
server library. All we do is add the TF-specific parts to the server.
"""
