// Dashboard: đọc report.json và hiển thị bảng so sánh + biểu đồ.
function dinhDang(n) {
  if (n === null || n === undefined) return "—";
  if (n >= 1000000) return (n / 1000000).toFixed(1) + " triệu";
  if (n >= 1000) return (n / 1000).toFixed(1) + " nghìn";
  return String(n);
}

function veBang(baoCao) {
  const ban = baoCao.trang_cua_ban;
  let html = "<table><tr><th>Trang</th><th>Người theo dõi</th><th>Bài mẫu</th>" +
    "<th>Thích TB / bài</th><th>Bình luận TB / bài</th><th>Tương tác TB</th><th>Trạng thái</th></tr>";
  html += `<tr><td><strong>${ban.ten} (bạn)</strong><br><a href="${ban.url}" target="_blank" rel="noopener">${ban.url}</a></td>` +
    `<td>${dinhDang(ban.nguoi_theo_doi)}</td><td>—</td><td>—</td><td>—</td><td>—</td><td>Trang của bạn</td></tr>`;
  for (const d of baoCao.doi_thu) {
    const tt = d.trang_thai === "co_du_lieu" ? "Có dữ liệu" : "Chưa có dữ liệu";
    html += `<tr><td><strong>${d.ten}</strong><br><a href="${d.url}" target="_blank" rel="noopener">${d.url}</a></td>` +
      `<td>${dinhDang(d.nguoi_theo_doi)}</td><td>${d.so_bai_mau || "—"}</td>` +
      `<td>${dinhDang(d.luot_thich_tb)}</td><td>${dinhDang(d.binh_luan_tb)}</td>` +
      `<td>${d.ty_le_tuong_tac_tb !== null && d.ty_le_tuong_tac_tb !== undefined ? d.ty_le_tuong_tac_tb + "%" : "—"}</td>` +
      `<td>${tt}</td></tr>`;
  }
  html += "</table>";
  document.getElementById("bang-so-sanh").innerHTML = html;
}

function veBieuDo(baoCao) {
  const tatCa = [{ ten: baoCao.trang_cua_ban.ten + " (bạn)", so: baoCao.trang_cua_ban.nguoi_theo_doi }]
    .concat(baoCao.doi_thu.map(d => ({ ten: d.ten, so: d.nguoi_theo_doi })));
  const lonNhat = Math.max(...tatCa.map(x => x.so || 0), 1);
  let html = "";
  for (const x of tatCa) {
    const pct = Math.max(1, Math.round((x.so || 0) / lonNhat * 100));
    html += `<div class="bar-row"><span class="ten">${x.ten}</span>` +
      `<div class="bar" style="width:${pct}%"></div><span class="so">${dinhDang(x.so)}</span></div>`;
  }
  document.getElementById("bieu-do").innerHTML = html;
}

function veBaiTotNhat(baoCao) {
  let html = "<table><tr><th>Trang</th><th>Bài tốt nhất trong mẫu</th><th>Thích</th><th>Bình luận</th></tr>";
  for (const d of baoCao.doi_thu) {
    const b = d.bai_tot_nhat;
    if (!b) {
      html += `<tr><td><strong>${d.ten}</strong></td><td colspan="3">Chưa có dữ liệu — ${d.ghi_chu || ""}</td></tr>`;
      continue;
    }
    html += `<tr><td><strong>${d.ten}</strong></td>` +
      `<td><a href="${b.url}" target="_blank" rel="noopener">${b.noi_dung || b.loai}</a><br><span class="luu-y">${b.thoi_gian || ""} · ${b.loai || ""}</span></td>` +
      `<td>${dinhDang(b.luot_thich)}</td><td>${dinhDang(b.binh_luan)}</td></tr>`;
  }
  html += "</table>";
  document.getElementById("bai-tot-nhat").innerHTML = html;
}

fetch("report.json")
  .then(r => { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
  .then(baoCao => {
    document.getElementById("ngay-bao-cao").textContent =
      "Báo cáo tạo ngày: " + (baoCao.ngay_tao || "").slice(0, 10) + " (giờ UTC).";
    veBang(baoCao);
    veBieuDo(baoCao);
    veBaiTotNhat(baoCao);
  })
  .catch(e => {
    document.getElementById("bang-so-sanh").innerHTML =
      "<p>Chưa tải được report.json (" + e.message + "). Hãy chạy <code>python3 analyzer.py</code> trước.</p>";
  });

document.getElementById("btn-them").addEventListener("click", () => {
  const link = document.getElementById("link-doi-thu").value.trim();
  const ketQua = document.getElementById("ket-qua-them");
  if (!link) { ketQua.textContent = "Bạn chưa dán link."; return; }
  let handle = link.replace(/^https?:\/\/(www\.)?facebook\.com\//, "").replace(/\/.*$/, "").replace(/[?#].*$/, "");
  if (!handle) { ketQua.textContent = "Link chưa đúng dạng facebook.com/ten-trang."; return; }
  ketQua.innerHTML = "Đã ghi nhận <strong>" + handle + "</strong>. Thêm đối thủ này vào " +
    "<code>competitors.json</code> (mục doi_thu, thêm ten + url + handle), rồi ghi số liệu " +
    "của 3–5 bài gần nhất vào <code>du_lieu_thu_cong.json</code> và chạy <code>python3 analyzer.py</code>.";
});
