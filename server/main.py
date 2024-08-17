import ast
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@dataclass
class Function:
    name: str
    line_number: int
    end_line_number: int


@dataclass
class Method(Function):
    pass


@dataclass
class Class:
    name: str
    line_number: int
    end_line_number: int
    methods: List[Method]


@dataclass
class Module:
    filename: str
    classes: List[Class]
    functions: List[Function]


class CodebaseVisitor(ast.NodeVisitor):
    def __init__(self):
        self.classes = []
        self.functions = []
        self.current_class = None

    def visit_ClassDef(self, node):
        methods = []
        old_class = self.current_class
        self.current_class = Class(
            name=node.name,
            line_number=node.lineno,
            end_line_number=node.end_lineno,
            methods=methods,
        )
        self.generic_visit(node)
        self.classes.append(self.current_class)
        self.current_class = old_class

    def visit_FunctionDef(self, node):
        if self.current_class:
            method = Method(
                name=node.name,
                line_number=node.lineno,
                end_line_number=(
                    node.end_lineno if hasattr(node, "end_lineno") else node.lineno
                ),
            )
            self.current_class.methods.append(method)
        else:
            function_obj = Function(
                name=node.name,
                line_number=node.lineno,
                end_line_number=(
                    node.end_lineno if hasattr(node, "end_lineno") else node.lineno
                ),
            )
            self.functions.append(function_obj)


def parse_file(filename: str) -> Module:
    with open(filename, "r") as file:
        content = file.read()

    tree = ast.parse(content)
    visitor = CodebaseVisitor()
    visitor.visit(tree)

    return Module(
        filename=filename, classes=visitor.classes, functions=visitor.functions
    )


def visualize_codebase(directory: str) -> List[Module]:
    modules = []
    ignore_dirs = {".venv", "venv", "node_modules", "__pycache__", ".git"}

    for root, dirs, files in os.walk(directory):
        # Remove ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                try:
                    module = parse_file(full_path)
                    modules.append(module)
                except Exception as e:
                    print(f"Error parsing {full_path}: {str(e)}")
                    continue
    return modules


class RepositoryPath(BaseModel):
    path: str


@app.post("/visualize")
async def visualize_repo(repo: RepositoryPath):
    if not os.path.isdir(repo.path):
        raise HTTPException(status_code=400, detail="Invalid repository path")

    modules = visualize_codebase(repo.path)

    # Convert dataclasses to dictionaries for JSON serialization
    result = []
    for module in modules:
        print("module", module)
        module_dict = {
            "filename": module.filename,
            "classes": [
                {
                    "name": cls.name,
                    "line_number": cls.line_number,
                    "end_line_number": cls.end_line_number,
                    "methods": [
                        {
                            "name": method.name,
                            "line_number": method.line_number,
                            "end_line_number": method.end_line_number,
                        }
                        for method in cls.methods
                    ],
                }
                for cls in module.classes
            ],
            "functions": [
                {
                    "name": func.name,
                    "line_number": func.line_number,
                    "end_line_number": func.end_line_number,
                }
                for func in module.functions
            ],
        }
        result.append(module_dict)

    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


# curl -X 'POST' \
#   'http://localhost:8000/visualize' \
#   -H 'accept: application/json' \
#   -H 'Content-Type: application/json' \
#   -d '{
#   "path": "/Users/galer7/p/repo-viewer"
# }'
