import argparse
import ast
import sys
import os

import astor


class CodeModifier:
    """A class to safely modify Python source code files."""

    def __init__(self, file_path):
        """Initializes the modifier with the path to a Python file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found at {file_path}")
        self.file_path = file_path
        with open(file_path, "r", encoding="utf-8") as f:
            self.source = f.read()
        self.tree = ast.parse(self.source, filename=self.file_path)

    def save(self, output_path=None):
        """Converts the modified AST back to source code and saves it."""
        if output_path is None:
            output_path = self.file_path

        modified_source = astor.to_source(self.tree)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(modified_source)
        print(f"Successfully saved modified code to {output_path}")

    def add_function(self, function_source):
        """Adds a new function to the end of the file."""
        try:
            # Parse the function source into an AST node
            function_tree = ast.parse(function_source)
            # The body of the parsed tree should contain our function definition
            if (
                not isinstance(function_tree, ast.Module)
                or not function_tree.body
            ):
                raise ValueError(
                    "The provided source is not a valid function definition."
                )

            new_function_node = function_tree.body[0]
            if not isinstance(
                new_function_node, (ast.FunctionDef, ast.AsyncFunctionDef)
            ):
                raise ValueError(
                    "The provided source is not a valid function definition."
                )

            # Add the new function node to the body of the main tree
            self.tree.body.append(new_function_node)
            print(
                f"Successfully added function '{new_function_node.name}' to the AST."
            )

        except (SyntaxError, IndexError) as e:
            raise ValueError(f"Invalid function source provided: {e}")


def main():
    """Main CLI handler for the code modifier."""
    parser = argparse.ArgumentParser(
        description="SMITH's Code Modifier. A tool for safe AST-based code modification."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 'add-function' command
    add_func_parser = subparsers.add_parser(
        "add-function", help="Add a new function to a file."
    )
    add_func_parser.add_argument(
        "file_path", help="The path to the Python file."
    )
    add_func_parser.add_argument(
        "--source-file",
        required=True,
        help="Path to a file containing the source code of the function to add.",
    )
    add_func_parser.add_argument(
        "--output", help="(Optional) Path to save the modified file."
    )

    args = parser.parse_args()

    try:
        modifier = CodeModifier(args.file_path)

        if args.command == "add-function":
            if not os.path.exists(args.source_file):
                raise FileNotFoundError(
                    f"Source file not found: {args.source_file}"
                )
            with open(args.source_file, "r", encoding="utf-8") as f:
                source_code = f.read()
            modifier.add_function(source_code)
            modifier.save(args.output)

    except (FileNotFoundError, SyntaxError, ValueError) as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
