## Mô tả thay đổi (Summary)
- **Người thực hiện:** [ ] Người A  |  [ ] Người B  |  [ ] Phần Chung
- **Use Case liên quan:** `UC-...`
- **Tóm tắt ngắn gọn:** 

---

## Danh sách kiểm tra trước khi Merge (Checklist)
- [ ] **Không xung đột vùng làm việc:** Chỉ chỉnh sửa các file thuộc phạm vi được phân công (hoặc đã trao đổi trước nếu sửa `[PHẦN CHUNG]`).
- [ ] **Tuân thủ kiến trúc:** Không viết truy vấn SQL/ORM trực tiếp trong `routers/`, mọi logic nghiệp vụ và `HTTPException` nằm trong `services/`.
- [ ] **Bảo mật:** Không push file `.env`, không trả về `password_hash` trong Response Schema.
- [ ] **Đã kiểm thử:** Đã chạy thử API trên Swagger UI (`/docs`) hoặc chạy `pytest` thành công.
