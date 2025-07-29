# Design Document: project_navigator.py

---

## 1. Strategic Need & Analogy

**Problem:** The agent currently has "tunnel vision," capable of analyzing only one file at a time. It lacks a holistic, architectural understanding of the codebase.

**Analogy:** The agent is a pedestrian in a large city. It can see the street it's on but has no map. `project_navigator.py` is the satellite cartographer that provides this map.

**Strategic Value:** This tool is the foundational component for the "Hands" evolution vector. It enables:
- **Impact Analysis:** Understanding the "blast radius" of any code change.
- **Safe Refactoring:** Ensuring all dependencies are identified before modification.
- **Intelligent Planning:** Allowing the agent to autonomously locate code relevant to a task.
- **Project Auditing:** Enabling the agent to self-onboard to new codebases.

---

## 2. Core Mechanism: AST, Not Regex

The tool will operate on a principle of high fidelity and reliability.

1.  **Recursive Scan:** It will walk a given project directory to find all `*.py` files.
2.  **AST Parsing:** Each file will be parsed into an Abstract Syntax Tree using Python's native `ast` library. This provides a 100% accurate, structured representation of the code, unlike fragile text-based parsing.
3.  **Entity Extraction:** The tool will traverse the AST to extract key nodes:
    - `ast.Import` & `ast.ImportFrom` (Imports)
    - `ast.ClassDef` (Classes)
    - `ast.FunctionDef` (Functions and Methods)
4.  **Map Aggregation:** The extracted data will be compiled into a single, structured JSON object.

---

## 3. Technical Specification

### 3.1. Command-Line Interface (CLI)

The tool will be invoked via `argparse`:

```bash
python project_navigator.py analyze <directory_path> --output <output_file.json>
```
- **`analyze`**: The primary command.
- **`<directory_path>`**: (Required) The absolute path to the project directory to be scanned.
- **`--output`**: (Optional) The path to the output JSON file. If omitted, the JSON will be printed to stdout.

### 3.2. Output Data Structure (JSON Map)

The output will be a JSON object with the following schema:

```json
{
  "project_name": "<Name of the scanned directory>",
  "analysis_timestamp": "<ISO 8601 UTC Timestamp>",
  "files": {
    "<absolute_path_to_file_1>": {
      "imports": ["<module1>", "<module2>"],
      "classes": [
        {
          "name": "<ClassName>",
          "methods": ["<method1>", "<method2>"]
        }
      ],
      "functions": ["<function1>"]
    },
    "<absolute_path_to_file_2>": {
      // ... structure repeats
    }
  }
}
```

---

## 4. Implementation Plan (MVP)

1.  **File Creation:** Create `project_navigator.py` in `SMITH_FRAMEWORK/smith_tools/`.
2.  **CLI Scaffolding:** Implement the `argparse` structure.
3.  **File Scanner:** Implement the recursive file discovery logic using `os.walk`.
4.  **AST Parser Core:** Implement the central function that takes a file path and returns a structured dictionary of its entities using `ast`.
5.  **Map Aggregator:** Implement the main loop that orchestrates the scanner and parser, compiling the final JSON map.
6.  **Initial Test:** Run the completed tool against the `QIKI_DTMP` project to verify the output.

