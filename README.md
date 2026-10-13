# Meinya Học

Dữ liệu của mục **Học** trên [elainabaka.com/hoc/](https://elainabaka.com/hoc/): sơ đồ khái niệm liên môn cho học sinh lớp 12
(Toán, Vật lí, Hóa học, sau này có Ngữ văn). Đây không phải kho đề thi: mỗi khái niệm có một câu định nghĩa viết lại bằng lời dễ hiểu,
lý do nên học nó năm 2026, một ví dụ, câu hỏi gợi ý và **nguồn** để tự kiểm. Các khái niệm nối với nhau qua các môn, ví dụ đạo hàm
(Toán) nối với vận tốc tức thời (Vật lí) và tốc độ phản ứng (Hóa học).

*English: open data (Vietnamese) behind the interactive grade-12 concept map at elainabaka.com/hoc/. Plain JSON, one file per subject,
every concept cites at least one source you can open.*

## Có gì

| Đường dẫn | Là gì |
|---|---|
| `data/schema.json` | Cấu trúc một file môn (JSON Schema draft 2020-12) |
| `data/toan-12.json` | Toán: cụm Đạo hàm, 15 khái niệm (gồm kiến thức nền lớp 11 và hai ứng dụng trong huấn luyện AI) |
| `data/ly-12.json`, `data/hoa-12.json` | Vật lí, Hóa học: hiện chỉ có các khái niệm mà cụm Đạo hàm trỏ tới |
| `tools/kiem.py` | Kiểm dữ liệu: đúng schema, cạnh trỏ tới nút có thật, mỗi nút có nguồn (chỉ dùng thư viện chuẩn Python) |
| `tests/test_kiem.py` | Test của `kiem.py` |

## Cấu trúc một file môn

```json
{"mon": "toan", "lop": 12, "ten": "Toán 12", "cap_nhat": "2026-10-13", "giay_phep": "CC BY-SA 4.0",
 "nodes": [{"id": "dao-ham", "ten": "Đạo hàm tại một điểm", "chuong": "Lớp 11 · Đạo hàm", "lop": 11, "loai": "khai-niem",
            "dinh_nghia": "một câu", "vi_sao_2026": "vì sao nên học", "vi_du": "một ví dụ có số",
            "cau_hoi": ["câu hỏi gợi ý"],
            "nguon": [{"ten": "OpenStax, Calculus Volume 1, mục 3.1", "url": "https://openstax.org/...", "doc": "2026-10-13"}],
            "x": 0.2, "y": 0.42}],
 "edges": [{"tu": "gioi-han", "toi": "dao-ham", "loai": "can-truoc"},
           {"tu": "dao-ham", "toi": "ly:van-toc-tuc-thoi", "loai": "lien-mon", "giai_thich": "v(t) = x'(t)"}]}
```

- **Nút** (`nodes`): `id` viết thường, nối bằng gạch ngang. `lop` của nút là lớp học khái niệm đó (file `toan-12` có cả kiến thức nền
  lớp 11). `loai` là `khai-niem` hoặc `ung-dung`. `x`, `y` (0 đến 1) là vị trí gợi ý trên sơ đồ chung của mọi môn.
- **Nguồn** (`nguon`): ít nhất một nguồn mỗi nút. Có `url` thì phải có `doc` (ngày đã mở trang để kiểm). Sách giáo khoa ghi tên bộ sách
  và bài, không kèm link. Chỗ chưa kiểm chắc ghi `"can_kiem": true` và nói rõ trong `ghi_chu`.
- **Cạnh** (`edges`): `can-truoc` (phải học `tu` trước `toi`), `dan-toi` (`tu` mở ra `toi`), `lien-mon` (`toi` dạng `mon:id`, nút nằm ở
  file môn kia, bắt buộc có `giai_thich`).

## Kiểm

```
py -3 -X utf8 tools/kiem.py
py -3 -X utf8 -m unittest discover -s tests -v
```

(Trên macOS/Linux dùng `python3` thay cho `py -3`.) `kiem.py` in số môn, nút, cạnh, nguồn và thoát mã 1 nếu có lỗi.

## Đóng góp

Thấy sai, thiếu nguồn hay muốn thêm khái niệm: mở issue hoặc pull request, hoặc gửi thư tới `meinya@elainabaka.com`.

1. Định nghĩa viết lại bằng lời của mình, không chép nguyên văn sách hay trang web.
2. Mỗi khái niệm có ít nhất một nguồn mở được; ghi ngày mở vào `doc`.
3. Chạy `tools/kiem.py` và test trước khi gửi.
4. Không đưa dữ liệu cá nhân vào kho.

## Giấy phép

- Nội dung (`data/`, tài liệu này): [Creative Commons Attribution-ShareAlike 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
  (CC BY-SA 4.0). Dùng lại thì ghi "Meinya Học, Elainabaka" kèm link elainabaka.com/hoc/ và chia sẻ bản sửa đổi cùng giấy phép.
- Mã (`tools/`, `tests/`): MIT.

Toàn văn hai giấy phép ở `LICENSE`. Các trang được trích làm nguồn thuộc về tác giả của chúng; kho này chỉ ghi tên và link.
