terraform {
  required_providers {
    helloworld = {
      source = "local/hello-world-provider"
      version = "0.1.0"
    }
  }
}

provider "helloworld" {
  foo = "bar"
}

resource helloworld_foo "foo" {
}
