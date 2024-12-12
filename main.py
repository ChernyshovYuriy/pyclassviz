import webbrowser

import javalang
from pyvis.network import Network

from utils import ensure_directory_exists, inject_fullscreen_css_js


def parse_java_class(java_class_path):
    with open(java_class_path, "r") as file:
        source_code = file.read()
    tree = javalang.parse.parse(source_code)
    return tree


def extract_methods_and_fields(tree):
    mf_fields = []
    mf_methods = []
    for path, node in tree:
        if isinstance(node, javalang.tree.FieldDeclaration):
            mf_fields.extend([var.name for var in node.declarators])
        elif isinstance(node, javalang.tree.MethodDeclaration):
            mf_methods.append(node.name)
    return mf_fields, mf_methods


def walk_tree(tree):
    nodes = [(None, tree)]
    while nodes:
        path, node = nodes.pop()
        yield path, node
        if isinstance(node, list):
            for child in node:
                nodes.append((node, child))
        elif hasattr(node, 'children'):
            for child in node.children:
                nodes.append((node, child))


def extract_relationships(tree):
    rltnshps = {}
    for node in tree.types:
        for method_i in node.methods:
            method_name = method_i.name
            rltnshps[method_name] = {"fields": {"read": set(), "write": set()}, "methods": set()}
            for parent, node_j in walk_tree(method_i):
                if isinstance(node_j, javalang.tree.MemberReference):
                    if isinstance(parent, javalang.tree.Assignment):
                        if node_j is parent.expressionl:
                            rltnshps[method_name]["fields"]["write"].add(node_j.member)
                        elif node_j is parent.value:
                            rltnshps[method_name]["fields"]["read"].add(node_j.member)
                    elif isinstance(parent, javalang.tree.BinaryOperation):
                        if node_j is parent.operandl or node_j is parent.operandr:
                            rltnshps[method_name]["fields"]["read"].add(node_j.member)

                    elif isinstance(parent, javalang.tree.StatementExpression):
                        if isinstance(parent.expression, javalang.tree.Unary):  # Correct way to check for unary ops
                            if isinstance(parent.expression.operand,
                                          javalang.tree.MemberReference) and parent.expression.operand is node_j:
                                if parent.expression.operator in ['++', '--']:
                                    rltnshps[method_name]["fields"]["read"].add(node_j.member)
                                    rltnshps[method_name]["fields"]["write"].add(node_j.member)
                                else:
                                    rltnshps[method_name]["fields"]["read"].add(node_j.member)
                    elif isinstance(parent, javalang.tree.MethodInvocation):
                        if node_j in parent.arguments:
                            rltnshps[method_name]["fields"]["read"].add(node_j.member)
                    elif parent is None:
                        pass
                    else:
                        rltnshps[method_name]["fields"]["read"].add(node_j.member)

                elif isinstance(node_j, javalang.tree.MethodInvocation):
                    rltnshps[method_name]["methods"].add(node_j.member)
    return rltnshps


def draw_with_pyvis(fields_in, methods_in, relationships_in):
    ensure_directory_exists("out")
    html_file_name = "out/class_diagram.html"
    net = Network(directed=True)

    # Add field nodes
    for field_l in fields_in:
        net.add_node(field_l, label=field_l, color="skyblue", shape="box")

    # Add method nodes
    for method_l in methods_in:
        net.add_node(method_l, label=method_l, color="lightgreen", shape="ellipse")

    # Add edges (with read/write distinction)
    for method_l, rel_l in relationships_in.items():
        for field_l in rel_l["fields"]["read"]:
            if field_l in fields_in:
                net.add_edge(method_l, field_l, title="Reads Field", color="blue")
            else:
                print(f"Missing field reference (read): {field_l}")
        for field_l in rel_l["fields"]["write"]:
            if field_l in fields_in:
                net.add_edge(method_l, field_l, title="Writes Field", color="red")
            else:
                print(f"Missing field reference (write): {field_l}")
        for called_method in rel_l["methods"]:
            if called_method in methods_in:
                net.add_edge(method_l, called_method, title="Calls Method")
            else:
                print(f"Missing method reference: {called_method}")

    print("Nodes:", net.nodes)
    print("Edges:", net.edges)
    net.write_html(html_file_name)
    inject_fullscreen_css_js(html_file_name)
    webbrowser.open(html_file_name)


file_path = "/home/yurii_backup/dev/phx-aosp/vendor/ford/packages/services/mediasourceservice/src/com/ford/internal/service/mediasourceservice/MediaSourceServiceImpl.java"
# file_path = "data/MediaInserter.java"
java_tree = parse_java_class(file_path)

fields, methods = extract_methods_and_fields(java_tree)
relationships = extract_relationships(java_tree)

print("Fields:", fields)
print("Methods:", methods)
print("Relationships:")
for method, rel in relationships.items():
    print(f"  {method}:")
    print(f"    Accessed Fields: {rel['fields']}")
    print(f"    Called Methods: {rel['methods']}")

draw_with_pyvis(fields, methods, relationships)
