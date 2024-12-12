import webbrowser

import javalang
from javalang.tree import MemberReference, Assignment, ConstructorDeclaration, MethodDeclaration, FieldDeclaration, \
    BinaryOperation, StatementExpression, MethodInvocation
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
        if isinstance(node, FieldDeclaration):
            mf_fields.extend([var.name for var in node.declarators])
        elif isinstance(node, MethodDeclaration):
            mf_methods.append(node.name)
        elif isinstance(node, ConstructorDeclaration):
            mf_methods.append(node.name)  # Constructors have a 'name' attribute
    return mf_fields, mf_methods


def walk_tree(tree):
    nodes = [(None, tree)]
    while nodes:
        parent, node = nodes.pop()
        yield parent, node
        if isinstance(node, list):
            for child in node:
                nodes.append((node, child))
        elif hasattr(node, 'children'):
            for child in node.children:
                if child:
                    nodes.append((node, child))


def extract_relationships(tree):
    rltnshps = {}
    for node in tree.types:
        for method_or_constructor in node.methods + node.constructors:
            if isinstance(method_or_constructor, MethodDeclaration):
                method_name = method_or_constructor.name
            elif isinstance(method_or_constructor, ConstructorDeclaration):
                method_name = "<init>"
            else:
                continue

            rltnshps[method_name] = {"fields": {"read": set(), "write": set()}, "methods": set()}
            for parent, node_j in walk_tree(method_or_constructor):
                if isinstance(node_j, MemberReference):
                    if isinstance(parent, Assignment):
                        if node_j is parent.expressionl:
                            rltnshps[method_name]["fields"]["write"].add(node_j.member)
                        elif node_j is parent.value:
                            rltnshps[method_name]["fields"]["read"].add(node_j.member)
                    elif isinstance(parent, BinaryOperation):
                        if node_j is parent.operandl or node_j is parent.operandr:
                            rltnshps[method_name]["fields"]["read"].add(node_j.member)
                    elif isinstance(parent, StatementExpression):
                        if hasattr(parent.expression, 'operator') and hasattr(parent.expression, 'operand'):
                            if isinstance(parent.expression.operand,
                                          MemberReference) and parent.expression.operand is node_j:
                                if parent.expression.operator in ['++', '--', '-', '+', '~', '!']:
                                    rltnshps[method_name]["fields"]["read"].add(node_j.member)
                                    if parent.expression.operator in ['++', '--']:
                                        rltnshps[method_name]["fields"]["write"].add(node_j.member)
                        elif isinstance(parent.expression, MemberReference):
                            rltnshps[method_name]["fields"]["write"].add(parent.expression.member)
                    elif isinstance(parent, MethodInvocation):
                        if node_j in parent.arguments:
                            rltnshps[method_name]["fields"]["read"].add(node_j.member)
                    elif parent is None:
                        pass
                    else:
                        rltnshps[method_name]["fields"]["read"].add(node_j.member)

                elif isinstance(node_j, MethodInvocation):
                    rltnshps[method_name]["methods"].add(node_j.member)
    return rltnshps


def draw_with_pyvis(fields_in, methods_in, relationships_in):
    ensure_directory_exists("out")
    html_file_name = "out/class_diagram.html"
    net = Network(directed=True, neighborhood_highlight=True)

    # Add field nodes
    for field_l in fields_in:
        net.add_node(field_l, label=field_l, color="skyblue", shape="box")

    # Add method nodes (handling <init>)
    method_labels = {}
    for method_l in methods_in:
        label = method_l
        if method_l == "<init>":
            label = "Constructor"
        net.add_node(method_l, label=label, color="lightgreen", shape="ellipse")
        method_labels[method_l] = label

    # Ensure <init> is in method_labels even if not in methods_in
    if "<init>" in relationships_in and "<init>" not in method_labels:
        net.add_node("<init>", label="Constructor", color="lightgreen", shape="ellipse")
        method_labels["<init>"] = "Constructor"
        methods_in.append("<init>")

    # Add edges (with read/write distinction) - Corrected Edge Labels
    for method_l, rel_l in relationships_in.items():
        if method_l not in method_labels:
            print(f"Warning: Method '{method_l}' not found in method_labels. Skipping edges for this method.")
            continue

        for field_l in rel_l["fields"]["read"]:
            if field_l in fields_in:
                net.add_edge(method_l, field_l, title="Reads Field", color="blue", label="R")  # Added label
            else:
                print(f"Warning: Field '{field_l}' (read by {method_l}) not found in fields_in.")
        for field_l in rel_l["fields"]["write"]:
            if field_l in fields_in:
                net.add_edge(method_l, field_l, title="Initializes Field", color="red",
                             label="W")  # Corrected title and added label
            else:
                print(f"Warning: Field '{field_l}' (written by {method_l}) not found in fields_in.")
        for called_method in rel_l["methods"]:
            if called_method in method_labels:
                net.add_edge(method_l, called_method, title="Calls Method", label="C")  # Added label
            else:
                print(f"Warning: Method '{called_method}' (called by {method_l}) not found in method_labels.")

    print("Nodes:", net.nodes)
    print("Edges:", net.edges)
    net.write_html(html_file_name)
    inject_fullscreen_css_js(html_file_name)
    webbrowser.open(html_file_name)


file_path = "data/DataProcessor.java"
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
