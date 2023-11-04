from tfprovider.rpc_plugin import RPCPluginServer


def main():
    s = RPCPluginServer()
    s.run()

if __name__ == "__main__":
    main()
