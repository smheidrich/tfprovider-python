terraform {
  required_providers {
    helloworld = {
      source = "local/hello-world-provider"
      version = "0.1.0"
    }
  }
}
