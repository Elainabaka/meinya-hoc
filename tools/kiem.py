"""Kiểm dữ liệu meinya-hoc: py -3 -X utf8 tools/kiem.py [thư_mục_data]

Kiểm mỗi file data/<mon>-<lop>.json:
  1. đúng data/schema.json (JSON Schema draft 2020-12, phần từ khóa schema này dùng);
  2. id nút không trùng; mỗi nút có ít nhất 1 nguồn; nguồn có url thì phải có ngày mở (doc);
  3. cạnh trỏ tới nút có thật: can-truoc / dan-toi trong cùng môn, lien-mon dạng mon:id sang môn khác và có giai_thich;
  4. không cạnh tự nối, không cạnh trùng.
Chỉ dùng thư viện chuẩn. Mã thoát 0 khi sạch, 1 khi có lỗi. Nguồn hay nút đánh "can_kiem": true được đếm và in ra (không phải lỗi).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"
TEN_FILE = re.compile(r"^(toan|ly|hoa|van)-(10|11|12)\.json$")

# Từ khóa schema mà bộ kiểm này hiểu. Schema dùng từ khóa khác thì dừng hẳn, để không có chuyện "tưởng đã kiểm".
TU_KHOA = {"$schema", "$id", "$defs", "$ref", "title", "description", "type", "properties", "required",
           "additionalProperties", "items", "minItems", "maxItems", "minLength", "maxLength", "pattern",
           "enum", "const", "minimum", "maximum"}


class SchemaKhongHo(Exception):
    """Schema dùng từ khóa mà bộ kiểm chưa hiểu."""


def _dung_kieu(v, kieu: str) -> bool:
    if kieu == "object":
        return isinstance(v, dict)
    if kieu == "array":
        return isinstance(v, list)
    if kieu == "string":
        return isinstance(v, str)
    if kieu == "boolean":
        return isinstance(v, bool)
    if kieu == "integer":
        return isinstance(v, int) and not isinstance(v, bool)
    if kieu == "number":
        return isinstance(v, (int, float)) and not isinstance(v, bool)
    if kieu == "null":
        return v is None
    raise SchemaKhongHo(f"type lạ: {kieu}")


def kiem_schema(v, sch: dict, goc: dict, duong: str = "$") -> list[str]:
    """Kiểm giá trị v theo schema con sch (goc là schema gốc để tra $ref). Trả về danh sách lỗi."""
    la = set(sch) - TU_KHOA
    if la:
        raise SchemaKhongHo(f"{duong}: từ khóa chưa hỗ trợ {sorted(la)}")
    if "$ref" in sch:
        ref = sch["$ref"]
        if not ref.startswith("#/$defs/"):
            raise SchemaKhongHo(f"{duong}: $ref chỉ hỗ trợ #/$defs/...")
        return kiem_schema(v, goc["$defs"][ref.split("/")[-1]], goc, duong)
    loi: list[str] = []
    if "type" in sch:
        kieu = sch["type"] if isinstance(sch["type"], list) else [sch["type"]]
        if not any(_dung_kieu(v, k) for k in kieu):
            return [f"{duong}: cần kiểu {'/'.join(kieu)}"]
    if "const" in sch and v != sch["const"]:
        loi.append(f"{duong}: phải là {sch['const']!r}")
    if "enum" in sch and v not in sch["enum"]:
        loi.append(f"{duong}: {v!r} không thuộc {sch['enum']}")
    if isinstance(v, str):
        if len(v) < sch.get("minLength", 0):
            loi.append(f"{duong}: ngắn hơn {sch['minLength']} ký tự")
        if "maxLength" in sch and len(v) > sch["maxLength"]:
            loi.append(f"{duong}: dài hơn {sch['maxLength']} ký tự")
        if "pattern" in sch and not re.search(sch["pattern"], v):
            loi.append(f"{duong}: {v!r} sai mẫu {sch['pattern']}")
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        if "minimum" in sch and v < sch["minimum"]:
            loi.append(f"{duong}: nhỏ hơn {sch['minimum']}")
        if "maximum" in sch and v > sch["maximum"]:
            loi.append(f"{duong}: lớn hơn {sch['maximum']}")
    if isinstance(v, list):
        if len(v) < sch.get("minItems", 0):
            loi.append(f"{duong}: cần ít nhất {sch['minItems']} phần tử")
        if "maxItems" in sch and len(v) > sch["maxItems"]:
            loi.append(f"{duong}: nhiều hơn {sch['maxItems']} phần tử")
        if "items" in sch:
            for i, x in enumerate(v):
                loi += kiem_schema(x, sch["items"], goc, f"{duong}[{i}]")
    if isinstance(v, dict):
        for k in sch.get("required", []):
            if k not in v:
                loi.append(f"{duong}: thiếu trường {k}")
        props = sch.get("properties", {})
        them = sch.get("additionalProperties", True)
        for k, x in v.items():
            if k in props:
                loi += kiem_schema(x, props[k], goc, f"{duong}.{k}")
            elif them is False:
                loi.append(f"{duong}: trường lạ {k}")
            elif isinstance(them, dict):
                loi += kiem_schema(x, them, goc, f"{duong}.{k}")
    return loi


def doc_mon(thu_muc: Path) -> tuple[dict[str, dict], list[str]]:
    """Đọc mọi data/<mon>-<lop>.json. Trả về {mon: dữ liệu} và lỗi đọc/tên file."""
    mon: dict[str, dict] = {}
    loi: list[str] = []
    for p in sorted(thu_muc.glob("*.json")):
        if p.name == "schema.json":
            continue
        if not TEN_FILE.match(p.name):
            loi.append(f"{p.name}: tên file phải là <mon>-<lop>.json")
            continue
        try:
            j = json.loads(p.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            loi.append(f"{p.name}: không đọc được JSON ({e})")
            continue
        j["_file"] = p.name
        key = j.get("mon") if isinstance(j, dict) else None
        if key in mon:
            loi.append(f"{p.name}: môn {key} đã có ở {mon[key]['_file']}")
            continue
        mon[str(key)] = j
    return mon, loi


def kiem(thu_muc: Path = DATA) -> tuple[list[str], dict]:
    """Kiểm cả thư mục data. Trả về (lỗi, thống kê)."""
    goc = json.loads((thu_muc / "schema.json").read_text(encoding="utf-8"))
    mon, loi = doc_mon(thu_muc)
    tk = {"mon": 0, "nut": 0, "nut_co_link": 0, "canh": 0, "lien_mon": 0, "nguon": 0, "nguon_url": 0, "can_kiem": 0}
    ids: dict[str, set[str]] = {}
    for key, j in mon.items():
        f = j["_file"]
        du_lieu = {k: v for k, v in j.items() if k != "_file"}
        loi += [f"{f}: {x}" for x in kiem_schema(du_lieu, goc, goc)]
        if not isinstance(j.get("nodes"), list):
            continue
        if f != f"{j.get('mon')}-{j.get('lop')}.json":
            loi.append(f"{f}: tên file không khớp mon/lop bên trong ({j.get('mon')}-{j.get('lop')})")
        ids[key] = set()
        tk["mon"] += 1
        for n in j["nodes"]:
            if not isinstance(n, dict):
                continue
            nid = n.get("id")
            if nid in ids[key]:
                loi.append(f"{f}: id nút trùng {nid}")
            ids[key].add(nid)
            tk["nut"] += 1
            tk["can_kiem"] += bool(n.get("can_kiem"))
            nguon = n.get("nguon") if isinstance(n.get("nguon"), list) else []
            if not nguon:
                loi.append(f"{f}: nút {nid} chưa có nguồn")
            tk["nut_co_link"] += any(isinstance(s, dict) and s.get("url") for s in nguon)
            for s in nguon:
                if not isinstance(s, dict):
                    continue
                tk["nguon"] += 1
                tk["can_kiem"] += bool(s.get("can_kiem"))
                if s.get("url"):
                    tk["nguon_url"] += 1
                    if not s.get("doc"):
                        loi.append(f"{f}: nút {nid}: nguồn có url phải ghi ngày mở (doc)")
    for key, j in mon.items():
        f = j["_file"]
        da_co = set()
        for e in j.get("edges", []) if isinstance(j.get("edges"), list) else []:
            if not isinstance(e, dict):
                continue
            tu, toi, loai = e.get("tu"), str(e.get("toi", "")), e.get("loai")
            tk["canh"] += 1
            if tu not in ids.get(key, set()):
                loi.append(f"{f}: cạnh từ nút không có: {tu}")
            if loai == "lien-mon":
                tk["lien_mon"] += 1
                m, _, nid = toi.partition(":")
                if not nid:
                    loi.append(f"{f}: cạnh liên môn {tu} -> {toi} phải dạng mon:id")
                elif m == key:
                    loi.append(f"{f}: cạnh liên môn {tu} -> {toi} trỏ về chính môn này")
                elif nid not in ids.get(m, set()):
                    loi.append(f"{f}: cạnh liên môn {tu} -> {toi}: không có nút {nid} trong môn {m}")
                if not e.get("giai_thich"):
                    loi.append(f"{f}: cạnh liên môn {tu} -> {toi} thiếu giai_thich")
            else:
                if ":" in toi:
                    loi.append(f"{f}: cạnh {loai} {tu} -> {toi} chỉ nối trong cùng môn (dùng lien-mon)")
                elif toi not in ids.get(key, set()):
                    loi.append(f"{f}: cạnh {tu} -> {toi}: không có nút {toi}")
            if tu == toi:
                loi.append(f"{f}: cạnh tự nối {tu}")
            if (tu, toi) in da_co:
                loi.append(f"{f}: cạnh trùng {tu} -> {toi}")
            da_co.add((tu, toi))
    return loi, tk


def main(argv: list[str]) -> int:
    thu_muc = Path(argv[1]) if len(argv) > 1 else DATA
    try:
        loi, tk = kiem(thu_muc)
    except SchemaKhongHo as e:
        print(f"Schema dùng thứ bộ kiểm chưa hiểu: {e}")
        return 1
    for x in loi:
        print("LỖI", x)
    print(f"{tk['mon']} môn, {tk['nut']} nút ({tk['nut_co_link']} nút có nguồn kèm link), {tk['canh']} cạnh ({tk['lien_mon']} liên môn), "
          f"{tk['nguon']} nguồn ({tk['nguon_url']} có link), {tk['can_kiem']} chỗ đánh can_kiem")
    print("Sạch." if not loi else f"{len(loi)} lỗi.")
    return 1 if loi else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
