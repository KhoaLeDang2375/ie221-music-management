# Hệ Thống Quản Lý Âm Nhạc Qua RESTful API (IE221)

Đồ án môn **Kỹ thuật lập trình Python (IE221)** – Chủ đề 2: Xây dựng Backend RESTful API Server quản lý thư viện âm nhạc và playlist cá nhân sử dụng **FastAPI**, **SQLAlchemy 2.0**, **PostgreSQL 16 (Docker)** và tích hợp **Groq API (Chatbot)**.

---

## 1. Tài Liệu Dự Án

* 📄 **Phân tích yêu cầu:** [`docs/Tai_lieu_phan_tich_yeu_cau.md`](docs/Tai_lieu_phan_tich_yeu_cau.md)
* 📐 **Thiết kế hệ thống (Kiến trúc + Sơ đồ lớp OOP + Đặc tả API):** [`docs/Tai_lieu_thiet_ke_he_thong.md`](docs/Tai_lieu_thiet_ke_he_thong.md)
* 🗄️ **Sơ đồ ERD Database (PDF):** [`database_diagram_music.pdf`](database_diagram_music.pdf)
* 🤝 **Quy tắc làm việc nhóm, chia file & Merge GitHub (Người A & Người B):** [`README_GIT_WORKFLOW.md`](README_GIT_WORKFLOW.md)

---

## 2. Cấu Trúc Thư Mục

```text
.
├── .github/
│   └── pull_request_template.md     # Checklist tự động khi tạo Pull Request
├── app/
│   ├── main.py                      # [PHẦN CHUNG] Khởi tạo ứng dụng FastAPI & đăng ký Router
│   ├── deps.py                      # [PHẦN CHUNG] Dependency Injection (get_db, get_current_user)
│   ├── core/                        # [PHẦN CHUNG] Cấu hình (.env) & Bảo mật (Bcrypt, JWT)
│   ├── db/                          # [PHẦN CHUNG] Khởi tạo SQLAlchemy Engine & Session
│   ├── models/                      # [PHẦN CHUNG] 9 lớp ORM ánh xạ 9 bảng PostgreSQL
│   ├── schemas/                     # [TÁCH A / B] Các lớp Pydantic kiểm tra dữ liệu vào/ra
│   ├── services/                    # [TÁCH A / B] Các lớp xử lý nghiệp vụ OOP (kế thừa BaseService)
│   └── routers/                     # [TÁCH A / B] Các RESTful API Endpoints
├── database/
│   ├── init/
│   │   ├── 01_chinook_original.sql          # Dữ liệu Chinook PostgreSQL gốc
│   │   └── 02_transform_schema_and_seed.sql # Script chuyển sang 9 bảng & tạo dữ liệu mẫu
│   └── README_DATABASE.md                   # Chi tiết về Database
├── docs/                            # Tài liệu Phân tích yêu cầu & Thiết kế hệ thống
├── tests/                           # Bộ kiểm thử tự động pytest (tách theo Người A / Người B)
├── compose.yaml                     # Cấu hình Docker Compose cho PostgreSQL 16
├── .env.example                     # Mẫu cấu hình biến môi trường
├── README.md                        # Tài liệu hướng dẫn chung (file này)
└── README_GIT_WORKFLOW.md           # Quy tắc chia việc, code và merge Git tránh conflict
```

---

## 3. Hướng Dẫn Khởi Chạy Database Trên Docker

### Bước 1: Tạo file biến môi trường `.env`
Sao chép từ file mẫu `.env.example`:

```powershell
# Trên Windows PowerShell
Copy-Item .env.example .env
```
*(Hoặc trên macOS/Linux: `cp .env.example .env`)*

### Bước 2: Khởi chạy container PostgreSQL 16
Đảm bảo Docker Desktop đang bật, sau đó chạy lệnh:

```powershell
docker compose up -d
```

Khi chạy lần đầu, Docker sẽ tự động nạp `01_chinook_original.sql` và `02_transform_schema_and_seed.sql` để tạo sẵn **9 bảng chuẩn**:
1. `app_user` (69 tài khoản mẫu, mật khẩu băm `bcrypt`)
2. `artist` (275 nghệ sĩ)
3. `album` (347 album)
4. `genre` (25 thể loại)
5. `media_type` (5 định dạng âm thanh)
6. `track` (3,503 bài hát – đã lược bỏ cột `bytes` và `unit_price`, đổi `milliseconds` thành `duration_ms`)
7. `playlist` (18 playlist mẫu đã gán `user_id`, `description`, `created_at`)
8. `playlist_track` (8,715 liên kết bài hát trong playlist kèm `added_at` và `ON DELETE CASCADE`)
9. `listening_history` (303 bản ghi lịch sử nghe nhạc mẫu)

### Bước 3: Kiểm tra Database đã sẵn sàng chưa
```powershell
docker exec music_management_db psql -U postgres -d music_db -c "\dt"
```

> [!TIP]
> **Làm mới (Reset) lại toàn bộ Database về trạng thái ban đầu:**
> Nếu trong lúc test bạn xóa/sửa dữ liệu và muốn khôi phục lại từ đầu, chỉ cần chạy:
> ```powershell
> docker compose down -v
> docker compose up -d
> ```

---

## 4. Kết Nối Database Bằng DBeaver

Mở **DBeaver** $\rightarrow$ **New Database Connection** $\rightarrow$ Chọn **PostgreSQL** và nhập thông số:

| Thông số | Giá trị mặc định (trong `.env`) |
| :--- | :--- |
| **Host** | `localhost` |
| **Port** | `5432` |
| **Database** | `music_db` |
| **Username** | `postgres` |
| **Password** | `postgres123` |

---

## 5. Danh Sách Tài Khoản Mẫu (Rule-based Users)

Tất cả tài khoản trong bảng `app_user` đều có mật khẩu được tạo theo quy tắc chung:
$$\texttt{<username>@123}$$

| `user_id` | `username` | Mật khẩu gốc | `role` | `is_active` | Mục đích sử dụng |
| :---: | :--- | :--- | :---: | :---: | :--- |
| `1` | `admin` | `admin@123` | `admin` | `true` | Tài khoản Quản trị viên mặc định |
| `2` | `testuser` | `testuser@123` | `user` | `true` | Tài khoản Người dùng mặc định (có sẵn 33 lượt nghe) |
| `3` | `andrew` | `andrew@123` | `admin` | `true` | Quản trị viên (từ Chinook Employee #1) |
| `11` | `luisg` | `luisg@123` | `user` | `true` | Người dùng thường (từ Chinook Customer #1) |
| `68` | `manoj.pareek` | `manoj.pareek@123` | `user` | **`false`** | Kiểm thử tài khoản bị khóa (`BR-06`, `UC-02`) |
| `69` | `puja_srivastava` | `puja_srivastava@123` | `user` | **`false`** | Kiểm thử tài khoản bị khóa (`BR-06`, `UC-02`) |
