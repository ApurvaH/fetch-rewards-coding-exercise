import yaml
from jsonschema import validate

with open("schema.yaml") as file:
    specification_schema = yaml.load(file, yaml.SafeLoader)


def validate_server(specification):
    validate(specification, specification_schema)
