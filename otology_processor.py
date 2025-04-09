import rdflib
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, OWL
from typing import List, Tuple, Optional, Dict, Any

class OntologyProcessor:
    def __init__(self):
        self.graph = Graph()
        self.namespaces = {} # To store namespaces for cleaner output

    def load_ontology(self, file_path: str, file_format: str = "turtle") -> bool:
        """Loads an ontology from a file."""
        try:
            self.graph = Graph() # Reset graph
            self.graph.parse(file_path, format=file_format)
            self.namespaces = dict(self.graph.namespaces())
            print(f"Ontology loaded successfully from {file_path}. Found {len(self.graph)} triples.")
            return True
        except Exception as e:
            print(f"Error loading ontology: {e}")
            self.graph = Graph() # Ensure graph is empty on failure
            return False

    def get_summary(self) -> Dict[str, int]:
        """Provides a basic summary of the ontology."""
        if not self.graph:
            return {"triples": 0, "classes": 0, "individuals": 0, "properties": 0}

        # Note: These counts can be approximations depending on ontology style (e.g. implicit classes)
        classes = set(self.graph.subjects(RDF.type, OWL.Class))
        individuals = set(self.graph.subjects(RDF.type, OWL.NamedIndividual))
        # More robust way to find individuals (anything with a type that isn't a Class/Property/Ontology)
        all_types = set(self.graph.objects(None, RDF.type))
        non_individual_types = {OWL.Class, RDFS.Class, OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty, OWL.Ontology, RDF.Property}
        potential_individual_types = all_types - non_individual_types
        individuals.update(s for s, o in self.graph.subject_objects(RDF.type) if o in potential_individual_types)

        obj_properties = set(self.graph.subjects(RDF.type, OWL.ObjectProperty))
        dt_properties = set(self.graph.subjects(RDF.type, OWL.DatatypeProperty))
        properties = obj_properties.union(dt_properties)

        return {
            "triples": len(self.graph),
            "classes": len(classes),
            "individuals": len(individuals),
            "properties": len(properties)
        }

    def get_classes(self) -> List[str]:
        """Returns a list of class URIs."""
        if not self.graph: return []
        return [str(cls) for cls in self.graph.subjects(RDF.type, OWL.Class)]

    def get_individuals(self) -> List[str]:
         """Returns a list of individual URIs."""
         if not self.graph: return []
         # More robust way needed here as well
         individuals = set(self.graph.subjects(RDF.type, OWL.NamedIndividual))
         all_types = set(self.graph.objects(None, RDF.type))
         non_individual_types = {OWL.Class, RDFS.Class, OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty, OWL.Ontology, RDF.Property}
         potential_individual_types = all_types - non_individual_types
         individuals.update(s for s, o in self.graph.subject_objects(RDF.type) if o in potential_individual_types and isinstance(s, URIRef))

         return [str(ind) for ind in individuals]


    def run_sparql_query(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Executes a SPARQL query and returns results."""
        if not self.graph:
            print("Cannot query, no ontology loaded.")
            return None
        try:
            results = self.graph.query(query)
            output = []
            for row in results:
                row_dict = {}
                # Use try-except for accessing potentially unbound variables
                for var in results.vars:
                   try:
                       val = row[var]
                       # Convert RDFLib terms to python types for easier display/JSON
                       if isinstance(val, URIRef):
                           row_dict[str(var)] = str(val)
                       elif isinstance(val, Literal):
                           row_dict[str(var)] = val.toPython()
                       else: # Blank nodes etc.
                           row_dict[str(var)] = str(val)
                   except KeyError:
                        row_dict[str(var)] = None # Variable was not bound in this row
                output.append(row_dict)
            return output
        except Exception as e:
            print(f"Error executing SPARQL query: {e}")
            return None

    def get_label(self, uri_str: str) -> Optional[str]:
        """Tries to get an rdfs:label for a given URI."""
        if not self.graph: return None
        try:
            uri = URIRef(uri_str)
            label = self.graph.value(subject=uri, predicate=RDFS.label)
            return str(label) if label else None
        except: # Handle invalid URIs etc.
            return None

    def add_triple(self, subj: str, pred: str, obj: str, is_object_literal: bool = False):
        """Adds a triple to the graph (basic). Needs proper URI handling."""
        if not self.graph: return False
        try:
            s = URIRef(subj) # Assuming subj/pred are URIs
            p = URIRef(pred)
            o = Literal(obj) if is_object_literal else URIRef(obj)
            self.graph.add((s, p, o))
            return True
        except Exception as e:
            print(f"Error adding triple: {e}")
            return False
