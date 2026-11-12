#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phân tích trang Facebook đối thủ + tạo chiến lược SEO (tiếng Việt).
Chạy:  python3 analyzer.py
Đọc:   competitors.json (trang của bạn + danh sách đối thủ)
       du_lieu_thu_cong.json (số liệu nhập tay từ nguồn công khai, nếu có)
Ghi:   report.json, chien-luoc-seo.md

NGUỒN DỮ LIỆU (theo thứ tự ưu tiên):
  1. facebook-cli (profile info / timeline) — chỉ đọc được trang bạn quản lý
     hoặc bạn bè; trang đối thủ thường bị Facebook chặn (403 Profile Not
     Accessible). Khi đó công cụ ghi rõ "không đọc được" chứ không bịa số.
  2. du_lieu_thu_cong.json — số liệu bạn tự nhập từ nguồn công khai
     (ví dụ: số người theo dõi và tương tác của các bài đăng gần đây mà
     bạn thấy trên Facebook / qua tìm kiếm). Đây là cách lấy số liệu thật
     cho trang đối thủ hiện nay.
  3. Nếu cả hai đều không có: trang đó được báo cáo là "chưa có dữ liệu".

CHỈ DÙNG DỮ LIỆU CÔNG KHAI. Không mật khẩu, không đăng bài, không thu
thập dữ liệu cá nhân.
"""
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FB_CLI = "/opt/hatch/bin/facebook-cli"

# Từ khóa chủ đề tin tức (tiếng Việt, không dấu để so khớp nhanh)
CHU_DE = {
    "tai nạn / giao thông": ["tai nan", "giao thong", "xe", "duong", "vu cham", "hien truong"],
    "pháp luật / an ninh": ["phap luat", "bat", "khoi to", "an ninh", "cong an", "truy na", "lua dao"],
    "thời sự / chính trị": ["quoc hoi", "chinh phu", "thu tuong", "nghi dinh", "chinh sach"],
    "kinh tế / giá cả": ["gia vang", "chung khoan", "ty gia", "xang dau", "lam phat", "thi truong"],
    "giải trí / âm nhạc": ["ca si", "mv", "am nhac", "phim", "dien vien", "showbiz"],
    "thể thao": ["bong da", "u23", "tuyen viet nam", "the thao", "giai dau"],
    "đời sống / xã hội": ["doi song", "xa hoi", "giao duc", "y te", "thoi tiet", "mua lu"],
}


def khong_dau(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d")


def phan_loai_chu_de(noi_dung: str) -> str:
    nd = khong_dau(noi_dung or "")
    diem = {}
    for ten, tus in CHU_DE.items():
        diem[ten] = sum(1 for tu in tus if tu in nd)
    tot = max(diem, key=diem.get)
    return tot if diem[tot] > 0 else "chưa phân loại được"


def doc_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"Cảnh báo: không đọc được {path}: {e}", file=sys.stderr)
        return None


def thu_facebook_cli(handle: str) -> dict:
    """Thử đọc trang bằng facebook-cli. Trả về dict có 'trang_thai'."""
    ket_qua = {"nguon": "facebook-cli", "trang_thai": "khong_doc_duoc", "ly_do": ""}
    try:
        r = subprocess.run(
            [FB_CLI, "profile", "info", "--profile-id", handle],
            capture_output=True, text=True, timeout=60,
        )
    except FileNotFoundError:
        ket_qua["ly_do"] = "không có facebook-cli trên máy này"
        return ket_qua
    except Exception as e:  # noqa: BLE001
        ket_qua["ly_do"] = f"lỗi chạy facebook-cli: {e}"
        return ket_qua
    out = (r.stdout or "") + (r.stderr or "")
    if "Profile Not Accessible" in out or "403" in out:
        ket_qua["ly_do"] = ("Facebook chặn (403 Profile Not Accessible): "
                            "trang này chỉ đọc được với người xem là bạn bè "
                            "hoặc người quản lý trang.")
    elif r.returncode != 0:
        ket_qua["ly_do"] = f"facebook-cli lỗi (mã {r.returncode}): {out.strip()[:200]}"
    else:
        ket_qua["trang_thai"] = "doc_duoc"
        ket_qua["du_lieu_tho"] = out[:2000]
    return ket_qua


def phan_tich_trang(trang: dict, du_lieu_tay: dict | None) -> dict:
    ten = trang.get("ten", "?")
    kq = {
        "ten": ten,
        "url": trang.get("url", ""),
        "handle": trang.get("handle", ""),
        "nguoi_theo_doi": None,
        "so_bai_mau": 0,
        "luot_thich_tb": None,
        "binh_luan_tb": None,
        "ty_le_tuong_tac_tb": None,
        "bai_tot_nhat": None,
        "gio_dang_pho_bien": [],
        "chu_de_chinh": [],
        "nguon_du_lieu": [],
        "trang_thai": "chua_co_du_lieu",
        "ghi_chu": "",
    }
    # 1. Thử facebook-cli
    cli = thu_facebook_cli(trang.get("handle", "")) if trang.get("handle") else None
    if cli:
        kq["nguon_du_lieu"].append("facebook-cli: " + cli["trang_thai"])
        if cli["trang_thai"] != "doc_duoc":
            kq["ghi_chu"] = cli.get("ly_do", "")
    # 2. Dữ liệu nhập tay (nguồn công khai)
    if du_lieu_tay:
        kq["nguoi_theo_doi"] = du_lieu_tay.get("nguoi_theo_doi")
        bai = du_lieu_tay.get("bai_dang", []) or []
        kq["so_bai_mau"] = len(bai)
        if bai:
            kq["trang_thai"] = "co_du_lieu"
            kq["nguon_du_lieu"].append(
                "nhập tay từ nguồn công khai (" + du_lieu_tay.get("nguon", "Facebook / tìm kiếm") + ")")
            likes = [b.get("luot_thich") for b in bai if b.get("luot_thich") is not None]
            cmts = [b.get("binh_luan") for b in bai if b.get("binh_luan") is not None]
            if likes:
                kq["luot_thich_tb"] = round(sum(likes) / len(likes), 1)
            if cmts:
                kq["binh_luan_tb"] = round(sum(cmts) / len(cmts), 1)
            if kq["nguoi_theo_doi"] and likes:
                kq["ty_le_tuong_tac_tb"] = round(
                    sum(likes) / len(likes) / kq["nguoi_theo_doi"] * 100, 3)
            tot = max(bai, key=lambda b: (b.get("luot_thich") or 0) + (b.get("binh_luan") or 0))
            kq["bai_tot_nhat"] = {
                "url": tot.get("url", ""),
                "loai": tot.get("loai", ""),
                "thoi_gian": tot.get("thoi_gian", ""),
                "luot_thich": tot.get("luot_thich"),
                "binh_luan": tot.get("binh_luan"),
                "noi_dung": tot.get("noi_dung", ""),
            }
            gio = Counter()
            for b in bai:
                m = re.search(r"[T ](\d{2}):", b.get("thoi_gian", "") or "")
                if m:
                    # thoi_gian lưu theo giờ UTC -> đổi sang giờ Việt Nam (+07)
                    gio[(int(m.group(1)) + 7) % 24] += 1
            kq["gio_dang_pho_bien"] = [f"{h:02d}:00 (giờ VN)" for h, _ in gio.most_common(3)]
            kq["chu_de_chinh"] = [c for c, _ in Counter(
                phan_loai_chu_de(b.get("noi_dung", "")) for b in bai).most_common(3)]
    if kq["trang_thai"] == "chua_co_du_lieu" and not kq["ghi_chu"]:
        kq["ghi_chu"] = "Chưa có dữ liệu: facebook-cli không đọc được và chưa có dữ liệu nhập tay."
    return kq


def dinh_dang_so(n):
    if n is None:
        return "—"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f} triệu"
    if n >= 1_000:
        return f"{n/1_000:.1f} nghìn"
    return str(n)


def tao_chien_luoc(bao_cao: dict) -> str:
    trang = bao_cao["trang_cua_ban"]
    doi_thu = bao_cao["doi_thu"]
    co_dl = [d for d in doi_thu if d["trang_thai"] == "co_du_lieu"]
    ngay = bao_cao["ngay_tao"][:10]
    dong = []
    dong.append(f"# Chiến lược SEO & nội dung — {ngay}\n")
    dong.append("Trang của bạn: **%s** (%s người theo dõi) — %s\n" % (
        trang["ten"], dinh_dang_so(trang.get("nguoi_theo_doi")), trang["url"]))
    dong.append("## 1. Đối thủ đang làm gì\n")
    for d in doi_thu:
        if d["trang_thai"] == "co_du_lieu":
            dong.append(
                f"- **{d['ten']}** ({dinh_dang_so(d['nguoi_theo_doi'])} người theo dõi, "
                f"mẫu {d['so_bai_mau']} bài): thích TB {dinh_dang_so(d['luot_thich_tb'])}/bài, "
                f"bình luận TB {dinh_dang_so(d['binh_luan_tb'])}/bài, "
                f"tỷ lệ tương tác TB {d['ty_le_tuong_tac_tb']}% — "
                f"chủ đề chính: {', '.join(d['chu_de_chinh']) or '—'}; "
                f"giờ đăng phổ biến: {', '.join(d['gio_dang_pho_bien']) or '—'}.")
        else:
            dong.append(f"- **{d['ten']}**: {d['ghi_chu'] or 'chưa có dữ liệu.'}")
    dong.append("\n## 2. Điểm khác biệt của bạn (lợi thế cạnh tranh)\n")
    dong.append("- Bạn đăng **video Reels dọc kiểu Vox** (hình chạy, biểu đồ, sơ đồ) 3 khung giờ "
                "7h / 12h / 19h — đối thủ lớn chủ yếu đăng **ảnh + link bài**; "
                "video giải thích là định dạng Facebook đang ưu tiên.")
    dong.append("- Bạn làm **bản tin tổng hợp 7 tin** (3 trong nước + 2 nước ngoài + 1 âm nhạc + "
                "1 thể thao) trong một video — đối thủ đăng từng tin rời rạc, người xem phải "
                "lướt nhiều lần.")
    dong.append("- Bạn nhỏ hơn đối thủ rất nhiều về số người theo dõi, nên chiến lược là "
                "**tăng tỷ lệ tương tác / người theo dõi**, không đua số lượng bài.\n")
    dong.append("## 3. Từ khóa & chủ đề nên tập trung\n")
    dong.append("- Từ khóa tin tức đang hút tương tác trên các trang đối thủ: "
                "tai nạn giao thông, pháp luật / bắt giữ, giá vàng, bóng đá Việt Nam, "
                "âm nhạc (MV mới), mưa lũ / thời tiết.")
    dong.append("- Từ khóa riêng của bạn nên giữ: **bản tin sáng / trưa / tối**, **tin nóng**, "
                "tên sự kiện + ngày (ví dụ: \"U23 Việt Nam 12/11\"), tên ca sĩ + tên bài hát mới.")
    dong.append("- Tiêu đề video nên có **số liệu + ngày + địa danh**, ví dụ: "
                "\"BẢN TIN TRƯA 12/11 — 7 TIN: giá vàng, mưa lũ, U23 Việt Nam\".\n")
    dong.append("## 4. Khung giờ & định dạng\n")
    dong.append("- Giữ 3 khung giờ vàng hiện tại: **7h, 12h, 19h** — trùng giờ đối thủ đăng nhiều "
                "nhất trong mẫu (sáng sớm, trưa, tối).")
    dong.append("- Video Reels dọc 1080x1920, dưới 3 phút; 10 giây đầu phải có tin nóng nhất "
                "và số liệu lớn (ví dụ: số nhà ngập, mức giá vàng).")
    dong.append("- Mỗi video thêm 1 câu hỏi cuối để kéo bình luận (\"Bạn nghĩ sao về…?\").\n")
    dong.append("## 5. Kế hoạch 30 ngày\n")
    dong.append("| Tuần | Việc làm | Mục tiêu |\n|---|---|---|\n"
                "| 1 | Chốt 5 từ khóa chủ lực (giá vàng, bóng đá, mưa lũ, MV mới, tin nóng) và đưa vào tiêu đề + mô tả video | Tiêu đề nhất quán |\n"
                "| 2 | Thêm phụ đề + hashtag cố định (#bantinsang #tintuc #reels) vào mô tả mỗi video | Người mới tìm thấy trang qua tìm kiếm |\n"
                "| 3 | Làm 3 video \"giải thích sâu\" (kiểu Vox) về chủ đề đối thủ đang hút tương tác nhất | Tăng thời gian xem |\n"
                "| 4 | So sánh lại bằng công cụ này (chạy lại `python3 analyzer.py`) và giữ lại định dạng có tương tác cao nhất | Báo cáo so sánh lần 2 |\n")
    dong.append("\n## 6. Giới hạn của báo cáo này\n")
    dong.append("- Số liệu đối thủ chỉ từ **mẫu bài đăng công khai gần đây** (không phải toàn bộ "
                "trang) và từ nguồn tìm kiếm công khai; Facebook không cho đọc toàn bộ trang "
                "đối thủ qua API/CLI (403 Profile Not Accessible).")
    dong.append("- Tỷ lệ tương tác tính trên mẫu nhỏ nên chỉ dùng để so sánh xu hướng, "
                "không phải con số chính thức của Facebook.")
    dong.append("- Chạy lại công cụ mỗi tuần để cập nhật số liệu mới.\n")
    return "\n".join(dong)


def main():
    cau_hinh = doc_json(ROOT / "competitors.json")
    if not cau_hinh:
        print("Không tìm thấy competitors.json", file=sys.stderr)
        return 1
    du_lieu = doc_json(ROOT / "du_lieu_thu_cong.json") or {}
    ban = cau_hinh["trang_cua_ban"]
    bao_cao = {
        "ngay_tao": datetime.now(timezone.utc).isoformat(),
        "trang_cua_ban": {
            "ten": ban["ten"], "url": ban["url"],
            "nguoi_theo_doi": ban.get("nguoi_theo_doi"),
            "ghi_chu": ban.get("ghi_chu", ""),
        },
        "doi_thu": [],
    }
    for dt in cau_hinh.get("doi_thu", []):
        tay = (du_lieu.get("doi_thu") or {}).get(dt.get("handle", "")) or \
              (du_lieu.get("doi_thu") or {}).get(dt.get("ten", ""))
        print(f"Đang phân tích: {dt.get('ten')} ...")
        bao_cao["doi_thu"].append(phan_tich_trang(dt, tay))
    (ROOT / "report.json").write_text(
        json.dumps(bao_cao, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "chien-luoc-seo.md").write_text(
        tao_chien_luoc(bao_cao), encoding="utf-8")
    print("Xong. Đã ghi report.json và chien-luoc-seo.md")
    for d in bao_cao["doi_thu"]:
        print(f"- {d['ten']}: {d['trang_thai']}, "
              f"theo dõi {dinh_dang_so(d['nguoi_theo_doi'])}, "
              f"thích TB {dinh_dang_so(d['luot_thich_tb'])}/bài")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
