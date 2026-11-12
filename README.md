# Phân tích đối thủ Facebook & Chiến lược SEO

Công cụ cho trang tin tức trên Facebook: so sánh trang của bạn với các trang
tin tức đối thủ, rồi tự tạo **chiến lược SEO & nội dung** bằng tiếng Việt.

Trang mẫu của công cụ: **Nguyen Binh Van (N News TV)** —
https://www.facebook.com/nguyen.binh.van.363133 (bản tin Reels 7h / 12h / 19h).

Trang dashboard chạy trực tiếp trên GitHub Pages:
https://binhnguyen25.github.io/facebook-competitor-seo/

## Công cụ làm gì

1. **Phân tích đối thủ**: số người theo dõi, số bài trong mẫu, lượt thích /
   bình luận trung bình mỗi bài, tỷ lệ tương tác, giờ đăng phổ biến, chủ đề
   chính, bài đăng tốt nhất.
2. **So sánh với trang của bạn**: bảng so sánh và biểu đồ người theo dõi.
3. **Tạo chiến lược SEO** (`chien-luoc-seo.md`): từ khóa nên tập trung, khung
   giờ & định dạng nên làm, mẫu tiêu đề video, kế hoạch 30 ngày.

## Cách chạy

```bash
python3 analyzer.py
```

Không cần cài thêm thư viện nào (chỉ dùng thư viện chuẩn của Python 3).
Kết quả ghi ra 2 file:

- `report.json` — dữ liệu phân tích (dashboard đọc file này)
- `chien-luoc-seo.md` — chiến lược SEO & nội dung bằng tiếng Việt

## Thêm / bớt đối thủ

1. Mở `competitors.json`, sửa mục `doi_thu`: mỗi đối thủ cần `ten`, `url`,
   `handle` (phần sau `facebook.com/`).
2. Ghi số liệu của đối thủ vào `du_lieu_thu_cong.json` (xem mẫu trong file):
   số người theo dõi + 3–5 bài gần nhất (thời gian, loại, lượt thích, bình
   luận, nội dung tóm tắt, link bài).
3. Chạy lại `python3 analyzer.py` và đẩy lên GitHub — dashboard tự cập nhật.

## Vì sao phải nhập số liệu tay?

Facebook **không cho** đọc trang đối thủ qua công cụ tự động:

- `facebook-cli` trả về lỗi **403 Profile Not Accessible** khi đọc trang
  đối thủ (kể cả trang công khai lớn như Tuổi Trẻ, Dân trí, VnExpress).
- Mở trang Facebook trên trình duyệt khi chưa đăng nhập cũng bị chặn.

Vì vậy công cụ thử `facebook-cli` trước, nếu bị chặn thì dùng số liệu bạn
nhập tay từ nguồn công khai (số người theo dõi và tương tác của các bài
đăng bạn thấy trên Facebook / qua tìm kiếm). Trang nào không có dữ liệu sẽ
được ghi rõ là **"không đọc được"** — công cụ không bao giờ bịa số liệu.

## Kết quả chạy thử (12/11/2026)

| Trang | Người theo dõi | Thích TB / bài | Bình luận TB / bài | Tỷ lệ tương tác TB |
|---|---:|---:|---:|---:|
| Tuổi Trẻ | 3,1 triệu | 710 | 12,3 | 0,023% |
| Dân trí | 2,3 triệu | 338 | 11 | 0,015% |
| VnExpress.net | 4,9 triệu | 4.800 | 94 | 0,098% |
| Nguyen Binh Van (bạn) | 13 nghìn | — | — | — |

Số liệu đối thủ lấy từ các bài đăng công khai ngày 10–12/11/2026 (mẫu nhỏ
1–3 bài/trang). Nhận xét chính: bài đăng ảnh + link của các báo lớn có tỷ
lệ tương tác rất thấp so với số người theo dõi (dưới 0,1%) — đây là cơ hội
cho định dạng video Reels giải thích (Vox) của trang bạn.

## Giới hạn

- Chỉ dùng dữ liệu công khai. Không mật khẩu, không đăng bài, không thu thập
  dữ liệu cá nhân.
- Số liệu là mẫu nhỏ (vài bài gần nhất), chỉ dùng để so sánh xu hướng, không
  phải con số chính thức của Facebook.
- Chạy lại công cụ mỗi tuần để cập nhật số liệu mới.

## Cấu trúc repo

| File | Để làm gì |
|---|---|
| `analyzer.py` | Code phân tích + tạo chiến lược SEO |
| `competitors.json` | Trang của bạn + danh sách đối thủ |
| `du_lieu_thu_cong.json` | Số liệu nhập tay từ nguồn công khai |
| `report.json` | Kết quả phân tích (được tạo ra khi chạy) |
| `chien-luoc-seo.md` | Chiến lược SEO (được tạo ra khi chạy) |
| `index.html`, `app.js` | Dashboard xem báo cáo trên GitHub Pages |
| `.github/workflows/deploy.yml` | Tự đăng dashboard lên GitHub Pages khi đẩy code |
