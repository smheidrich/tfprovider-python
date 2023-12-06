"""
Library that allows creating Terraform providers in Python.

While development is still going on, the library is divided into "levels" to
clearly separate different degrees of syntactic sugar from each other and from
lower-level "unsugared" APIs.

The hope is that, eventually, these levels will collapse to a simple 2-level
split between "core" and "sugar" components. Maybe this will involve creating
two completely separate PyPI packages as well.
"""
