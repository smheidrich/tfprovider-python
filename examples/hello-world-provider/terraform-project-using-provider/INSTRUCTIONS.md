Add this section to your `~/.terraformrc` to allow loading the example provider
from your local filesystem, adjusting the path to the repository:

```hcl
provider_installation {
  dev_overrides {
    "local/hello-world-provider" = "/path/to/this/repo/examples/hello-world-provider/terraform-plugin"
  }

  direct {}
}
```

Then you can run Terraform from within this directory (skipping the usual
`init` step because that doesn't work with local overrides):

```bash
terraform apply
```

If there is an error, re-run with the `TF_LOG=debug` env var set to see the
provider's output:

```bash
TF_LOG=debug terraform apply
```
