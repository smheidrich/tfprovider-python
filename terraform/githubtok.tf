provider "githubfinetok" {
}

# TODO this has a bootstrapping problem in that the GitHub provider itself
#   needs it, so when this gets (re)created, tf apply will fail due to the
#   GitHub resource refresh not working with the unknown value. workaround
#   is to only apply this resource and nothing else, which can be done via
#   apply-github-tokens-only.sh
resource githubfinetok_token "create_project_token" {
  provider = githubfinetok
  name = "create-${var.project_name}"
  expires = "2024-12-10"
  write_permissions = ["administration", "contents"]
}

resource githubfinetok_token "mirror_token" {
  provider = githubfinetok
  name = "mirror-${var.project_name}"
  expires = "2024-12-10"
  write_permissions = ["contents", "actions"]
  select_repositories = [var.project_name]
}
