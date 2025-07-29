import argparse
import ast
import sys
import os


class CodeVisitor(ast.NodeVisitor):
    """
    A node visitor to find all functions, classes, and their methods.
    """

    def __init__(self):
        self.structure = {"classes": [], "functions": []}

    def visit_ClassDef(self, node):
        class_methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                class_methods.append(item.name)

        self.structure["classes"].append(
            {
                "name": node.name,
                "methods": class_methods,
                "lineno": node.lineno,
            }
        )
        # We don't call generic_visit for classes to avoid double-counting methods as global functions

    def visit_FunctionDef(self, node):
        # This will only visit top-level functions because we skip generic_visit in visit_ClassDef
        self.structure["functions"].append(
            {"name": node.name, "lineno": node.lineno}
        )
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        # This will also only visit top-level async functions
        self.structure["functions"].append(
            {"name": node.name, "lineno": node.lineno}
        )
        self.generic_visit(node)


def analyze_code(source_code, file_name="<string>"):
    """
    Analyzes Python source code and extracts its structure.
    Returns a dictionary with classes and functions.
    Raises exceptions on failure.
    """
    try:
        tree = ast.parse(source_code, filename=file_name)
        visitor = CodeVisitor()
        visitor.visit(tree)
        return visitor.structure
    except (SyntaxError, UnicodeDecodeError) as e:
        raise ValueError(f"Error parsing file {file_name}: {e}")
    except Exception as e:
        raise RuntimeError(
            f"An unexpected error occurred during analysis: {e}"
        )


def analyze_file(file_path):
    """
    Reads a Python file and analyzes its structure.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found at {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    return analyze_code(source, file_name=file_path)


def main():
    """
    Main CLI handler for the context engine.
    """
    parser = argparse.ArgumentParser(
        description="SMITH's Context Engine. A tool for intelligent code analysis."
    )
    parser.add_argument(
        "file_path", help="The absolute path to the Python file to analyze."
    )

    args = parser.parse_args()

    try:
        analysis_result = analyze_file(args.file_path)

        print(f"Analysis for: {args.file_path}")
        print("=" * 40)

        if analysis_result["classes"]:
            print("Classes found:")
            for cls in sorted(
                analysis_result["classes"], key=lambda x: x["lineno"]
            ):
                print(f"  - [L{cls['lineno']}] class {cls['name']}:")
                for method in sorted(cls["methods"]):
                    print(f"    - {method}()")
        else:
            print("No classes found.")

        print("-" * 40)

        if analysis_result["functions"]:
            print("Functions found:")
            for func in sorted(
                analysis_result["functions"], key=lambda x: x["lineno"]
            ):
                print(f"  - [L{func['lineno']}] {func['name']}()")
        else:
            print("No functions found.")

    except (ValueError, FileNotFoundError, RuntimeError) as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
