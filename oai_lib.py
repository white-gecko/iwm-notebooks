import io
from sickle import Sickle
from sickle.iterator import OAIItemIterator
from sickle.models import Record
import lxml.etree as etree
from rdflib import Graph
from rdflib.tools.rdf2dot import rdf2dot
import pydotplus
from IPython.display import display, Code, Image
from html import escape

def display_xmls_tree(xml_string, rankdir="TB"):
    x = etree.fromstring(str(xml_string))
    display_xml_tree(x, rankdir)

def display_oai_tree(oai_object, rankdir="TB"):
    if isinstance(oai_object, OAIItemIterator):
        oai_object = oai_object.oai_response
    display_xml_tree(oai_object.xml, rankdir)

def display_xml_tree(xml_tree, rankdir="TB"):
    nodes: Dict[Node, str] = {}

    def node(x) -> str:
        if x not in nodes:
            nodes[x] = f"node{len(nodes)}"
        return nodes[x]

    stream = io.StringIO()

    stream.write('digraph { \n node [ fontname="DejaVu Sans" ] ; \n')
    stream.write(f"rankdir={rankdir}; \n")
    for elem in xml_tree.iter():
        parent = elem.getparent()
        if parent is None:
            continue
        pn = node(parent)
        cn = node(elem)
        stream.write(f"\t{pn} -> {cn} ;\n")

    for u, n in nodes.items():
        stream.write("# %s %s\n" % (u, n))
        f = [
            f"<tr><td align='left'>{k}:</td><td align='left'>\"{v}\"</td></tr>"
            for k,v in sorted(u.attrib.items())
        ]
        if u.text is not None:
            f.append(f"<tr><td align='left' colspan='2'><I>{escape(u.text)}</I></td></tr>")
        localname = escape(etree.QName(u).localname)
        attributes = "".join(f)
        stream.write(
            f"{n} [ shape=none, label=< <table color='#666666' cellborder='0' cellspacing='0' border='1'><tr><td colspan='2' bgcolor='grey'><B>{localname}</B></td></tr>{attributes}</table> > ] \n"
        )
    stream.write("}\n")

    dg = pydotplus.graph_from_dot_data(stream.getvalue())
    png = dg.create_png()
    display(Image(png))

def display_xmls(xml_string):
    x = etree.fromstring(str(xml_string))
    display_xml(x)

def display_oai(oai_object):
    if isinstance(oai_object, OAIItemIterator):
        oai_object = oai_object.oai_response
    display_xml(oai_object.xml)

def display_xml(xml_tree):
    display(Code(data=etree.tostring(xml_tree, pretty_print=True).decode(), language="xml"))

def display_turtle(graph):
    display(Code(data=graph.serialize(format="turtle"), language="turtle"))

def display_graph(g):
    stream = io.StringIO()
    rdf2dot(g, stream, opts = {"rankdir": "LR"})
    dg = pydotplus.graph_from_dot_data(stream.getvalue())
    png = dg.create_png()
    display(Image(png))

class Found( Exception ):
    def __init__(self, found):
        self.found = found

class EdmRecord(Record):
    """Represents an OAI record with EDM metadata.

    Check out [sickle.models.Record](https://sickle.readthedocs.io/en/latest/api.html#sickle.models.Record)
    """

    def __iter__(self):
        return iter(self.metadata.items()) if PY3 else \
            self.metadata.iteritems()

    def get_metadata(self):
        # We want to get record/metadata/
        # and parse it to an RDF graph
        g = Graph()
        metadata = self.xml.find('.//' + self._oai_namespace + 'metadata').getchildren()[0]
        rdf_string = etree.tostring(metadata).decode()
        g.parse(data=rdf_string, format="xml")
        return g


class LidoRecord(Record):
    """Represents an OAI record with LIDO metadata.

    Check out [sickle.models.Record](https://sickle.readthedocs.io/en/latest/api.html#sickle.models.Record)
    """

    def get_metadata(self):
        # We want to get record/metadata/
        # and get it as xml tree
        metadata = self.xml.find('.//' + self._oai_namespace + 'metadata').getchildren()[0]
        return metadata

def get_sickle(oai_url, metadataPrefix):
    sickle = Sickle(oai_url)
    if metadataPrefix == "edm":
        sickle.class_mapping['ListRecords'] = EdmRecord
        sickle.class_mapping['GetRecord'] = EdmRecord
    if metadataPrefix == "lido":
        sickle.class_mapping['ListRecords'] = LidoRecord
        sickle.class_mapping['GetRecord'] = LidoRecord
    return sickle
