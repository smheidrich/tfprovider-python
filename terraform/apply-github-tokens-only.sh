#!/bin/bash
# see comment in githubtok.tf
terraform plan -target githubfinetok_token.create_project_token -out ghtok.tfplan \
&& terraform apply ghtok.tfplan \
&& rm -f ghtok.tfplan
