import logging
from pathlib import Path
from typing import Dict
import typer
from typing_extensions import Annotated
import json

import yaml


DEFAULT_PREFIXES = {
    "intermine": "https://w3id.org/intermine/",
    "linkml": "https://w3id.org/linkml/",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "schema": "http://schema.org/",
    "bibo": "http://purl.org/ontology/bibo/",
    "NCIT": "http://purl.obolibrary.org/obo/NCIT_",
    "SIO": "http://semanticscience.org/resource/SIO_",
    "foaf": "http://xmlns.com/foaf/0.1/",
    "OIO": "http://www.geneontology.org/formats/oboInOwl#",
    "EDAM": "http://edamontology.org/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
    "RO": "http://purl.obolibrary.org/obo/RO_",
    "GENO": "http://purl.obolibrary.org/obo/GENO_",
    "ERO": "http://purl.obolibrary.org/obo/ERO_",
    "uniprot.core": "http://purl.uniprot.org/core/",
    "SO": "http://purl.obolibrary.org/obo/SO_",
    "ECO": "http://purl.obolibrary.org/obo/ECO_"
}


def translate_model(input_obj: Dict, linkml_obj: Dict) -> None:
    """
    Translate an input model into a corresponding LinkML schema.

    Args:
        input_obj: The input InterMine model object
        output_obj: The LinkML schema object

    """
    if 'model' in input_obj:
        input_model = input_obj['model']
    else:
        input_model = input_obj
    for class_name, class_obj in input_model['classes'].items():
        class_definition = {
            'name': class_name,   
        }
        if 'extends' in class_obj and class_obj['extends']:
            class_definition['is_a'] = class_obj['extends'][0]
        if 'term' in class_obj:
            class_definition['class_uri'] = class_obj['term'].strip()
        if 'displayName' in class_obj:
            if class_obj['displayName'] != class_name:
                if 'aliases' not in class_definition:
                    class_definition['aliases'] = []
                class_definition['aliases'].append(class_obj['displayName'])
        class_definition['slots'] = []
        class_definition['slot_usage'] = {}
        linkml_obj['classes'][class_name] = class_definition

        # Parse attributes
        if 'attributes' in class_obj:
            for attribute, attribute_obj in class_obj['attributes'].items():
                class_definition['slots'].append(attribute)
                slot_definition = {}
                if 'type' in attribute_obj:
                    range = get_linkml_type(attribute_obj['type'])
                    slot_definition['range'] = range
                if 'term' in attribute_obj:
                    slot_uri = attribute_obj['term'].strip()
                    slot_definition['slot_uri'] = slot_uri
                class_definition['slot_usage'][attribute] = slot_definition
                linkml_obj['slots'][attribute] = {}

        # Parse references
        if 'references' in class_obj:
            for reference, reference_obj in class_obj['references'].items():
                if reference not in class_definition['slots']:
                    class_definition['slots'].append(reference)
                slot_definition = {}
                if 'displayName' in reference_obj:
                    slot_definition['aliases'] = []
                    if reference_obj['displayName'] != reference:
                        if 'aliases' not in slot_definition:
                            slot_definition['aliases'] = []
                        slot_definition['aliases'].append(reference_obj['displayName'])
                if 'referencedType' in reference_obj:
                    range = reference_obj['referencedType']
                    slot_definition['range'] = range
                if 'term' in reference_obj:
                    slot_uri = reference_obj['term'].strip()
                    slot_definition['slot_uri'] = slot_uri
                slot_definition['multivalued'] = False
                if reference in class_definition['slot_usage']:
                    raise Exception(f"Overwriting existing slot usage for '{reference}' when parsing reference")
                class_definition['slot_usage'][reference] = slot_definition
                linkml_obj['slots'][reference] = {}

        # Parse collections
        if 'collections' in class_obj:
            for collection, collection_obj in class_obj['collections'].items():
                if collection not in class_definition['slots']:
                    class_definition['slots'].append(collection)
                slot_definition = {}
                if 'displayName' in collection_obj:
                    slot_definition['aliases'] = []
                    if collection_obj['displayName'] != collection:
                        if 'aliases' not in slot_definition:
                            slot_definition['aliases'] = []
                        slot_definition['aliases'].append(collection_obj['displayName'])
                if 'referencedType' in collection_obj:
                    range = collection_obj['referencedType']
                    slot_definition['range'] = range
                if 'term' in collection_obj:
                    slot_uri = collection_obj['term'].strip()
                    slot_definition['slot_uri'] = slot_uri
                slot_definition['multivalued'] = True
                if collection in class_definition['slot_usage']:
                    raise Exception(f"Overwriting existing slot usage for '{collection}' when parsing collection")
                class_definition['slot_usage'][collection] = slot_definition
                linkml_obj['slots'][collection] = {}


def serialize(obj, filename, indent=2) -> None:
    """
    Serialize a given object as YAML.

    Args:
        obj: The object to serialize
        filename: The filename to write to
        indent: Indentation level for YAML

    """
    if filename.endswith('.json'):
        with open(filename, 'w') as file:
            json.dump(obj, file, indent=indent)
    else:
        with open(filename, 'w') as file:
            yaml.dump(obj, file, indent=indent)


def get_linkml_type(java_type: str) -> str:
    """
    Get LinkML type corresponding to InterMine type.

    Args:
        java_type: The java-specific data type from InterMine

    """
    if java_type == 'java.lang.String':
        linkml_type = 'string'
    elif java_type in {'java.lang.Integer', 'int'}:
        linkml_type = 'integer'
    elif java_type == 'java.lang.Double':
        linkml_type = 'double'
    elif java_type == 'java.lang.Boolean':
        linkml_type = 'boolean'
    else:
        #default to string
        linkml_type = 'string'
    return linkml_type


def main(
        input: Annotated[Path, typer.Argument(help="The input filename")],
        output: Annotated[str, typer.Argument(help="The output filename")],
        id: Annotated[str, typer.Argument(help="A machine-readable ID of the schema")],
        name: Annotated[str, typer.Argument(help="The title of the schema (should be URL friendly)")],
        prefix: Annotated[str, typer.Argument(help="The prefix for the schema")],
        iri: Annotated[str, typer.Argument(help="The base IRI for the schema")],
        version: Annotated[str, typer.Argument(help="The version of the schema")],
        description: Annotated[str, typer.Argument(help="The description of the schema")],
        license: Annotated[str, typer.Argument(help="The license for the schema")],
    ) -> None:
    """
    Parse a given InterMine Model JSON into LinkML Schema.

    Example:

    python intermine2linkml.py flymine_model.json flymine.yaml flymine FlyMine flymine https://flymine.org/ 0.0.1 "FlyMine Data Model" https://creativecommons.org/publicdomain/zero/1.0/
    """
    model_obj = json.load(open(input))
    linkml_obj = {
        'id': id,
        'name': name,
        'version': version,
        'description': description,
        'license': license
    }
    linkml_obj['default_prefix'] = prefix
    linkml_obj['default_range'] = 'string'
    linkml_obj['classes'] = {}
    linkml_obj['slots'] = {}
    linkml_obj['types'] = {}
    linkml_obj['prefixes'] = DEFAULT_PREFIXES
    linkml_obj['prefixes'][prefix] = iri
    translate_model(model_obj, linkml_obj)
    serialize(linkml_obj, output)


if __name__ == "__main__":
    typer.run(main)