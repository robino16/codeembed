"""Generates __init__.py files for each package under src/codeembed/ by re-exporting
all public classes and functions found in that package's modules."""

import ast
from pathlib import Path

ROOT = Path(__file__).parent.parent
CODEEMBED_SRC = ROOT / "src" / "codeembed"


def public_names(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    return [
        node.name
        for node in tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_")
    ]


def write_init(package_dir: Path, imports: list[tuple[str, list[str]]]) -> None:
    seen: set[str] = set()
    lines = []
    for module, names in imports:
        unique = [n for n in names if n not in seen]
        seen.update(unique)
        if unique:
            lines.append(f"from {module} import {', '.join(sorted(unique))}")
    if not lines:
        (package_dir / "__init__.py").write_text("", encoding="utf-8")
        return
    all_names = sorted(seen)
    all_list = "__all__ = [\n" + "".join(f'    "{n}",\n' for n in all_names) + "]\n"
    content = "\n".join(lines) + "\n\n" + all_list
    (package_dir / "__init__.py").write_text(content, encoding="utf-8")


def process_package(package_dir: Path) -> list[str]:
    package = ".".join(package_dir.relative_to(ROOT / "src").parts)
    imports: list[tuple[str, list[str]]] = []

    for module_file in sorted(package_dir.glob("*.py")):
        if module_file.name == "__init__.py":
            continue
        names = public_names(module_file)
        if names:
            module = f"{package}.{module_file.stem}"
            imports.append((module, names))

    write_init(package_dir, imports)
    return [name for _, names in imports for name in names]


def main() -> None:
    top_level_imports: list[tuple[str, list[str]]] = []

    for package_dir in sorted(CODEEMBED_SRC.iterdir()):
        if not package_dir.is_dir() or not (package_dir / "__init__.py").exists():
            continue
        names = process_package(package_dir)
        if names:
            package = ".".join(package_dir.relative_to(ROOT / "src").parts)
            top_level_imports.append((package, names))

    write_init(CODEEMBED_SRC, top_level_imports)
    print("Done.")


if __name__ == "__main__":
    main()
