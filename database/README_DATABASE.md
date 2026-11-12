# Hướng Dẫn Cơ Sở Dữ Liệu (PostgreSQL + Docker + DBeaver)

Cơ sở dữ liệu của **Hệ thống quản lý âm nhạc** được xây dựng từ **Chinook Database** và đã được chuẩn hóa theo đúng **Tài liệu Phân tích Yêu cầu** (9 bảng, lược bỏ 4 bảng bán hàng, bổ sung `app_user` với mật khẩu rule-base và `listening_history` kèm mock data).

---

## 1. Khởi chạy Database trên Docker

Từ thư mục gốc của repo (`project/`), tạo file `.env` từ `.env.example` và chạy lệnh:

```powershell
Copy-Item .env.example .env
docker compose up -d
```

Lần đầu tiên khởi chạy, container `music_management_db` (`postgres:16-alpine`) sẽ tự động chạy 2 script trong `database/init/`:
1. `01_chinook_original.sql`: Nạp dữ liệu Chinook gốc.
2. `02_transform_schema_and_seed.sql`: Chuyển đổi sang **9 bảng chuẩn**, tạo tài khoản rule-base từ `employee`/`customer`, xóa 4 bảng bán hàng, thiết lập khóa ngoại (`ON DELETE RESTRICT` / `ON DELETE CASCADE`) và tạo 303 dòng dữ liệu mẫu cho `listening_history`.

> [!TIP]
> Nếu bạn muốn **reset lại toàn bộ database về trạng thái ban đầu**, chạy:
> ```powershell
> docker compose down -v
> docker compose up -d
> ```

---

## 2. Kết nối bằng DBeaver để xem ERD & chỉnh sửa

Mở **DBeaver** $\rightarrow$ **New Database Connection** $\rightarrow$ Chọn **PostgreSQL** và nhập:

| Thông số | Giá trị |
| :--- | :--- |
| **Host** | `localhost` |
| **Port** | `5432` |
| **Database** | `music_db` |
| **Username** | `postgres` |
| **Password** | `postgres123` |

* Sau khi kết nối, mở `music_db` $\rightarrow$ `Schemas` $\rightarrow$ `public` $\rightarrow$ Nhấp đúp vào `Tables` và chọn tab **ER Diagram** để xem toàn bộ sơ đồ 9 bảng và các đường nối khóa ngoại (hoặc xem file `database_diagram_music.pdf`).

---

## 3. Danh sách Tài khoản Mẫu & Quy tắc Mật khẩu (Rule-base)

Toàn bộ mật khẩu trong bảng `app_user` đều được băm bằng thuật toán **bcrypt** (`$2a$10$...`) theo quy tắc:
$$\text{Mật khẩu} = \texttt{<username>@123}$$

| `user_id` | `username` | `email` | Mật khẩu gốc | `role` | `is_active` | Ghi chú |
| :---: | :--- | :--- | :--- | :---: | :---: | :--- |
| `1` | `admin` | `admin@music.local` | `admin@123` | `admin` | `true` | Admin mặc định |
| `2` | `testuser` | `testuser@music.local` | `testuser@123` | `user` | `true` | User mặc định (có sẵn 33 lượt nghe) |
| `3` | `andrew` | `andrew@chinookcorp.com` | `andrew@123` | `admin` | `true` | Từ Chinook Employee #1 |
| `4` | `nancy` | `nancy@chinookcorp.com` | `nancy@123` | `admin` | `true` | Từ Chinook Employee #2 |
| `5..10` | `jane`, `margaret`, ... | `<username>@chinookcorp.com` | `<username>@123` | `user` | `true` | Từ Chinook Employee #3..8 |
| `11..67` | `luisg`, `ftremblay`, ... | Email gốc từ Chinook Customer | `<username>@123` | `user` | `true` | Từ Chinook Customer #1..57 |
| `68` | `manoj.pareek` | `manoj.pareek@rediff.com` | `manoj.pareek@123` | `user` | **`false`** | Dùng để test tài khoản bị khóa (`BR-06`) |
| `69` | `puja_srivastava` | `puja_srivastava@yahoo.in` | `puja_srivastava@123` | `user` | **`false`** | Dùng để test tài khoản bị khóa (`BR-06`) |
