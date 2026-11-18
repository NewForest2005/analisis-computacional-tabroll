from pathlib import Path
import re


def rtf_text(text: str) -> str:
    out = []
    for ch in text:
        code = ord(ch)
        if ch == "\\":
            out.append(r"\\")
        elif ch == "{":
            out.append(r"\{")
        elif ch == "}":
            out.append(r"\}")
        elif ch == "\t":
            out.append(r"\tab ")
        elif code < 128:
            out.append(ch)
        else:
            signed = code if code <= 32767 else code - 65536
            out.append(rf"\u{signed}?")
    return "".join(out)


source = Path("referencias_compiladas_proyecto.md").read_text(encoding="utf-8")
lines = source.splitlines()
parts = [
    r"{\rtf1\ansi\deff0",
    r"{\fonttbl{\f0 Aptos;}}",
    r"\viewkind4\uc1\lang3082",
]

for line in lines:
    stripped = line.strip()
    if not stripped:
        parts.append(r"\par")
        continue
    if stripped.startswith("# "):
        parts.append(r"\pard\sb240\sa120\b\fs32 " + rtf_text(stripped[2:]) + r"\b0\fs22\par")
    elif stripped.startswith("## "):
        parts.append(r"\pard\sb180\sa80\b\fs27 " + rtf_text(stripped[3:]) + r"\b0\fs22\par")
    elif stripped.startswith("### "):
        parts.append(r"\pard\sb120\sa60\b\fs24 " + rtf_text(stripped[4:]) + r"\b0\fs22\par")
    elif stripped.startswith("- "):
        text = stripped[2:]
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 — \2", text)
        text = text.replace("**", "").replace("*", "")
        parts.append(r"\pard\li360\fi-180 \bullet\~" + rtf_text(text) + r"\par")
    elif stripped.startswith("> "):
        parts.append(r"\pard\li360\ri360\i " + rtf_text(stripped[2:]) + r"\i0\par")
    elif stripped == "---":
        parts.append(r"\pard\brdrb\brdrs\brdrw10\par")
    else:
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 — \2", stripped)
        text = text.replace("**", "").replace("*", "")
        parts.append(r"\pard\sa80 " + rtf_text(text) + r"\par")

parts.append("}")
Path(".tmp_refs/referencias_compiladas_proyecto.rtf").write_text("\n".join(parts), encoding="ascii")
