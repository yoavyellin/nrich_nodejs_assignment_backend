from get_deps import get_deps


class DependenciesGraph:
    def __init__(self, root_package):
        self.root_package = root_package
        self.nodes = [
            {
                "id": root_package,
                "symbolType": "diamond",  # unique shape for the root
                "color": "#fff",  # unique color for the root
            }
        ]
        self.links = []

    def generate_graph(self, package=None):
        """
        THE ALGORITHM:

        1. Get package deps
        2. For each dep:
            2.1. If dep does exist in self.nodes, add link to self.links and return.
            2.2. if dep doesn't exist in self.nodes, add it there, add link to self.links
                 and recursively call this function on this new node.

        """
        current_package = self.root_package if not package else package
        current_package_deps = get_deps(current_package)

        for dep in current_package_deps:
            if not self.check_if_node_exists(dep):
                # Then add the node and recursively call this function on dep
                self.add_node(dep)
                self.generate_graph(package=dep)

            self.add_link(current_package, dep)

    def add_link(self, source, target):
        self.links.append(
            {
                "source": source,
                "target": target,
            }
        )

    def add_node(self, package):
        self.nodes.append(
            {
                "id": package,
                "symbolType": "circle",
                "color": "#4f46e5",
            }
        )

    def check_if_node_exists(self, package_name):
        for node in self.nodes:
            if node.get("id") == package_name:
                return True
        return False
