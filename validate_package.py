import json
import pathlib
import re
import py_compile

root = pathlib.Path(__file__).parent
for path in [root / "skill.json", root / "interactionModels/custom/en-US.json", root / "interactionModels/custom/pt-BR.json"]:
    json.loads(path.read_text(encoding="utf-8"))
py_compile.compile(str(root / "lambda/lambda_function.py"), doraise=True)
text_files = [p for p in root.rglob("*") if p.is_file() and p.suffix in {".json", ".py", ".md", ".txt", ".example", ""}]
all_text = "\n".join(p.read_text(encoding="utf-8") for p in text_files)
assert not re.search(r"AIza[0-9A-Za-z_-]{20,}", all_text)
assert not (root / "lambda/.env").exists()
print("Package validation passed")
