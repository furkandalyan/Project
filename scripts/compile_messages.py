#!/usr/bin/env python
import os
import struct


def compile_mo(po_path, mo_path):
    messages = {}
    msgid = None
    msgstr = None

    def _unquote(s):
        if s.startswith('"') and s.endswith('"'):
            s = s[1:-1]
        return s.replace(r"\\n", "\n").replace(r'\\"', '"')

    with open(po_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            if line.startswith("msgid "):
                if msgid is not None and msgstr is not None:
                    messages[msgid] = msgstr
                msgid = _unquote(line[5:].strip())
                msgstr = ""
            elif line.startswith("msgstr "):
                msgstr = _unquote(line[6:].strip())
            elif line.startswith('"') and msgid is not None and msgstr is not None:
                # Continuation line
                if msgstr == "":
                    msgid += _unquote(line)
                else:
                    msgstr += _unquote(line)

    if msgid is not None and msgstr is not None:
        messages[msgid] = msgstr

    # Build .mo binary
    keys = sorted(messages.keys())
    ids = [k.encode("utf-8") for k in keys]
    strs = [messages[k].encode("utf-8") for k in keys]

    keystart = 7 * 4
    id_offset = keystart
    str_offset = id_offset + len(keys) * 8
    id_str_offset = str_offset + len(keys) * 8

    ids_lens = []
    offset = 0
    for s in ids:
        ids_lens.append((len(s), id_str_offset + offset))
        offset += len(s) + 1

    strs_lens = []
    offset = 0
    for s in strs:
        strs_lens.append((len(s), id_str_offset + sum(len(x) + 1 for x in ids) + offset))
        offset += len(s) + 1

    output = []
    output.append(struct.pack("Iiiiiii", 0x950412de, 0, len(keys), id_offset, str_offset, 0, 0))
    for length, off in ids_lens:
        output.append(struct.pack("ii", length, off))
    for length, off in strs_lens:
        output.append(struct.pack("ii", length, off))
    for s in ids:
        output.append(s + b"\0")
    for s in strs:
        output.append(s + b"\0")

    os.makedirs(os.path.dirname(mo_path), exist_ok=True)
    with open(mo_path, "wb") as f:
        f.write(b"".join(output))


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    locale_dir = os.path.join(base_dir, "locale")
    for root, _, files in os.walk(locale_dir):
        for name in files:
            if not name.endswith(".po"):
                continue
            po_path = os.path.join(root, name)
            mo_path = os.path.join(root, name[:-3] + ".mo")
            compile_mo(po_path, mo_path)
            print(f"Compiled: {po_path} -> {mo_path}")


if __name__ == "__main__":
    main()
