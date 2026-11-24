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
│   │   ├── 02_transform_schema_and_seed.sql # Script chuyển sang 9 bảng & tạo dữ liệu mẫu
│   │   └── 03_seed_vietnamese_music.sql     # Bổ sung thể loại, nghệ sĩ, album, bài hát tiếng Việt
│   └── README_DATABASE.md                   # Chi tiết về Database
├── docs/                            # Tài liệu Phân tích yêu cầu & Thiết kế hệ thống
├── postman/                         # Postman Collection & Environment kiểm thử 17 Use Cases
├── tests/                           # Bộ kiểm thử tự động pytest (tách theo Người A / Người B)
├── compose.yaml                     # Cấu hình Docker Compose (PostgreSQL 16 + FastAPI Backend)
├── Dockerfile                       # Đóng gói image Backend FastAPI
├── pytest.ini                       # Cấu hình pytest
├── requirements.txt                 # Thư viện Python cho Backend & kiểm thử
├── .env.example                     # Mẫu cấu hình biến môi trường
├── README.md                        # Tài liệu hướng dẫn chung (file này)
└── README_GIT_WORKFLOW.md           # Quy tắc chia việc, code và merge Git tránh conflict
```

---

## 3. Khởi Chạy Nhanh Toàn Hệ Thống Bằng Docker (1 Lệnh — `NFR-04`)

### Bước 1: (Tùy chọn) Tạo file biến môi trường `.env`
Nếu muốn đổi secret key hoặc điền `GROQ_API_KEY` thật để test API Chatbot (`UC-12`), sao chép từ file mẫu `.env.example`:

```powershell
# Trên Windows PowerShell
Copy-Item .env.example .env
```
*(Trên macOS/Linux: `cp .env.example .env`. Nếu bỏ qua bước này, `compose.yaml` vẫn dùng sẵn bộ cấu hình mặc định an toàn để chạy local ngay lập tức.)*

### Bước 2: Khởi chạy đồng thời PostgreSQL 16 và FastAPI Backend
Đảm bảo Docker Desktop đang bật, sau đó chạy **một lệnh duy nhất**:

```powershell
docker compose up -d --build
```

Khi chạy lần đầu, Docker sẽ tự động:
1. Nạp `01_chinook_original.sql`, `02_transform_schema_and_seed.sql` và `03_seed_vietnamese_music.sql` để tạo **9 bảng chuẩn**:
   - `app_user` (69 tài khoản mẫu, mật khẩu băm `bcrypt`)
   - `artist` (281 nghệ sĩ, gồm 275 Chinook + 6 nghệ sĩ Việt)
   - `album` (353 album)
   - `genre` (29 thể loại, gồm 25 gốc + 4 thể loại nhạc Việt)
   - `media_type` (5 định dạng âm thanh)
   - `track` (3,527 bài hát – 3,503 Chinook + 24 bài hát tiếng Việt có dấu)
   - `playlist` (18 playlist mẫu)
   - `playlist_track` (8,715 liên kết bài hát trong playlist)
   - `listening_history` (303 bản ghi lịch sử nghe nhạc mẫu)
2. Build và khởi chạy container `music_management_api` (FastAPI) sau khi Database đã `healthy`.

### Bước 3: Kiểm tra API & Database
* **Healthcheck API + DB:** http://localhost:8000/health
* **Swagger UI (Interactive Docs):** http://localhost:8000/docs
* **Kiểm tra trạng thái container:**
  ```powershell
  docker compose ps
  ```

> [!TIP]
> **Làm mới (Reset) lại toàn bộ Database về trạng thái ban đầu:**
> ```powershell
> docker compose down -v
> docker compose up -d --build
> ```

---

## 4. Kết Nối Database Bằng DBeaver

Mở **DBeaver** $\rightarrow$ **New Database Connection** $\rightarrow$ Chọn **PostgreSQL** và nhập thông số:

| Thông số | Giá trị mặc định |
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

---

## 6. Chạy Kiểm Thử Tự Động (`pytest`)

* **Chạy trực tiếp trong container Docker (khuyến nghị, không cần cài Python trên máy):**
  ```powershell
  docker compose exec api pytest -v
  ```
* **Hoặc chạy trên máy local (sau khi đã bật `db` và cài `requirements.txt` trong `.venv`):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\python.exe -m pip install -r requirements.txt
  .\.venv\Scripts\python.exe -m pytest -v
  ```

---

## 7. Kiểm Thử Bằng Postman

1. Mở **Postman** $\rightarrow$ **Import** $\rightarrow$ chọn 2 file trong thư mục `postman/`:
   * [`postman/IE221_Music_Management.postman_collection.json`](postman/IE221_Music_Management.postman_collection.json)
   * [`postman/IE221_Local.postman_environment.json`](postman/IE221_Local.postman_environment.json)
2. Chọn Environment **`IE221 Music Management - Local`** ở góc phải trên.
3. Chạy lần lượt thư mục **`1. Auth`** (tự động lưu `user_token` và `admin_token`) rồi chạy các thư mục còn lại hoặc bấm **Run collection**.
