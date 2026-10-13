"""Test của tools/kiem.py: py -3 -X utf8 -m unittest discover -s tests -v (chạy ở gốc repo)."""
from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC / "tools"))

import kiem  # noqa: E402


class DuLieuThat(unittest.TestCase):
    """Dữ liệu đang có trong data/ phải sạch và đủ yêu cầu bước 1."""

    def test_sach(self):
        loi, tk = kiem.kiem(GOC / "data")
        self.assertEqual(loi, [])
        self.assertEqual(tk["nut"], tk["nut_co_link"], "mọi nút cần ít nhất một nguồn có link đã mở")

    def test_cum_dao_ham(self):
        toan = json.loads((GOC / "data" / "toan-12.json").read_text(encoding="utf-8"))
        self.assertTrue(12 <= len(toan["nodes"]) <= 15)
        lien_mon = [e for e in toan["edges"] if e["loai"] == "lien-mon"]
        self.assertGreaterEqual(len(lien_mon), 3)
        mon_dich = {e["toi"].split(":")[0] for e in lien_mon}
        self.assertTrue({"ly", "hoa"} <= mon_dich)
        self.assertTrue(any(n.get("loai") == "ung-dung" for n in toan["nodes"]))

    def test_mot_cau_dinh_nghia(self):
        for p in (GOC / "data").glob("*-*.json"):
            for n in json.loads(p.read_text(encoding="utf-8"))["nodes"]:
                self.assertTrue(n["vi_sao_2026"].strip())
                self.assertLessEqual(len(n["dinh_nghia"]), 600)


class LoiBiBat(unittest.TestCase):
    """Sửa hỏng một bản sao của data/ thì kiem phải báo lỗi."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        for p in (GOC / "data").glob("*.json"):
            shutil.copy(p, self.tmp / p.name)
        self.toan = json.loads((self.tmp / "toan-12.json").read_text(encoding="utf-8"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def ghi(self, du_lieu: dict, ten: str = "toan-12.json") -> list[str]:
        (self.tmp / ten).write_text(json.dumps(du_lieu, ensure_ascii=False), encoding="utf-8")
        return kiem.kiem(self.tmp)[0]

    def test_ban_sao_sach(self):
        self.assertEqual(self.ghi(self.toan), [])

    def test_thieu_nguon(self):
        d = copy.deepcopy(self.toan)
        d["nodes"][0]["nguon"] = []
        loi = self.ghi(d)
        self.assertTrue(any("chưa có nguồn" in x for x in loi), loi)

    def test_url_khong_co_ngay_mo(self):
        d = copy.deepcopy(self.toan)
        d["nodes"][1]["nguon"] = [{"ten": "Một trang", "url": "https://example.org/a"}]
        self.assertTrue(any("ngày mở" in x for x in self.ghi(d)))

    def test_url_khong_phai_https(self):
        d = copy.deepcopy(self.toan)
        d["nodes"][1]["nguon"][0]["url"] = "javascript:alert(1)"
        self.assertTrue(any("sai mẫu" in x for x in self.ghi(d)))

    def test_canh_toi_nut_khong_co(self):
        d = copy.deepcopy(self.toan)
        d["edges"].append({"tu": "dao-ham", "toi": "khong-co", "loai": "dan-toi"})
        self.assertTrue(any("không có nút khong-co" in x for x in self.ghi(d)))

    def test_lien_mon_toi_nut_khong_co(self):
        d = copy.deepcopy(self.toan)
        d["edges"].append({"tu": "dao-ham", "toi": "ly:khong-co", "loai": "lien-mon", "giai_thich": "thử lỗi"})
        self.assertTrue(any("không có nút khong-co trong môn ly" in x for x in self.ghi(d)))

    def test_lien_mon_thieu_giai_thich(self):
        d = copy.deepcopy(self.toan)
        for e in d["edges"]:
            if e["loai"] == "lien-mon":
                del e["giai_thich"]
                break
        self.assertTrue(any("thiếu giai_thich" in x for x in self.ghi(d)))

    def test_can_truoc_khong_duoc_sang_mon_khac(self):
        d = copy.deepcopy(self.toan)
        d["edges"].append({"tu": "dao-ham", "toi": "ly:van-toc-tuc-thoi", "loai": "can-truoc"})
        self.assertTrue(any("chỉ nối trong cùng môn" in x for x in self.ghi(d)))

    def test_id_trung(self):
        d = copy.deepcopy(self.toan)
        d["nodes"].append(copy.deepcopy(d["nodes"][0]))
        self.assertTrue(any("id nút trùng" in x for x in self.ghi(d)))

    def test_schema_truong_la_va_id_sai_mau(self):
        d = copy.deepcopy(self.toan)
        d["nodes"][0]["la"] = 1
        d["nodes"][1]["id"] = "Dao Ham"
        loi = self.ghi(d)
        self.assertTrue(any("trường lạ la" in x for x in loi), loi)
        self.assertTrue(any("sai mẫu" in x for x in loi), loi)

    def test_toa_do_ngoai_khung(self):
        d = copy.deepcopy(self.toan)
        d["nodes"][0]["x"] = 1.5
        self.assertTrue(any("lớn hơn 1" in x for x in self.ghi(d)))

    def test_ten_file_khong_khop(self):
        (self.tmp / "toan-12.json").rename(self.tmp / "toan-11.json")
        loi = kiem.kiem(self.tmp)[0]
        self.assertTrue(any("không khớp mon/lop" in x for x in loi), loi)

    def test_json_hong(self):
        (self.tmp / "hoa-12.json").write_text("{", encoding="utf-8")
        loi = kiem.kiem(self.tmp)[0]
        self.assertTrue(any("không đọc được JSON" in x for x in loi), loi)

    def test_main_tra_ma_1_khi_loi(self):
        d = copy.deepcopy(self.toan)
        d["nodes"][0]["nguon"] = []
        self.ghi(d)
        self.assertEqual(kiem.main(["kiem.py", str(self.tmp)]), 1)
        self.assertEqual(kiem.main(["kiem.py", str(GOC / "data")]), 0)


class BoKiemSchema(unittest.TestCase):
    def test_tu_khoa_chua_ho_tro_thi_dung(self):
        with self.assertRaises(kiem.SchemaKhongHo):
            kiem.kiem_schema(1, {"oneOf": []}, {})

    def test_bool_khong_phai_so_nguyen(self):
        self.assertTrue(kiem.kiem_schema(True, {"type": "integer"}, {}))
        self.assertEqual(kiem.kiem_schema(3, {"type": "integer", "minimum": 1}, {}), [])


if __name__ == "__main__":
    unittest.main()
