/*******************************************************************************
   Music Management System - Vietnamese Music Seed Data (NFR-05, Q-03)
   Appends Vietnamese genres, artists, albums, and 24 Vietnamese tracks
   without modifying existing Chinook IDs.
********************************************************************************/

BEGIN;

-- 1. Vietnamese Genres
INSERT INTO genre (name)
VALUES
    ('Nhạc Trẻ'),
    ('Nhạc Trữ Tình'),
    ('Rap Việt'),
    ('Indie Việt')
ON CONFLICT (name) DO NOTHING;

-- 2. Vietnamese Artists
INSERT INTO artist (name)
VALUES
    ('Sơn Tùng M-TP'),
    ('Đen Vâu'),
    ('Mỹ Tâm'),
    ('Hà Anh Tuấn'),
    ('Hoàng Thùy Linh'),
    ('Vũ.')
ON CONFLICT (name) DO NOTHING;

-- 3. Vietnamese Albums
INSERT INTO album (title, artist_id)
SELECT v.title, a.artist_id
FROM (
    VALUES
        ('Chúng Ta Của Hiện Tại (Tuyển Tập)', 'Sơn Tùng M-TP'),
        ('Show Của Đen', 'Đen Vâu'),
        ('Tâm 9', 'Mỹ Tâm'),
        ('Truyện Ngắn', 'Hà Anh Tuấn'),
        ('Hoàng', 'Hoàng Thùy Linh'),
        ('Một Vạn Năm', 'Vũ.')
) AS v(title, artist_name)
JOIN artist a ON a.name = v.artist_name
WHERE NOT EXISTS (
    SELECT 1 FROM album al WHERE al.artist_id = a.artist_id AND al.title = v.title
);

-- 4. 24 Vietnamese Tracks (full UTF-8 diacritics)
INSERT INTO track (name, album_id, media_type_id, genre_id, composer, duration_ms)
SELECT
    v.track_name,
    al.album_id,
    mt.media_type_id,
    g.genre_id,
    v.composer,
    v.duration_ms
FROM (
    VALUES
        ('Chạy Ngay Đi', 'Chúng Ta Của Hiện Tại (Tuyển Tập)', 'Sơn Tùng M-TP', 'Nhạc Trẻ', 'Nguyễn Thanh Tùng', 248000),
        ('Nơi Này Có Anh', 'Chúng Ta Của Hiện Tại (Tuyển Tập)', 'Sơn Tùng M-TP', 'Nhạc Trẻ', 'Nguyễn Thanh Tùng', 260000),
        ('Lạc Trôi', 'Chúng Ta Của Hiện Tại (Tuyển Tập)', 'Sơn Tùng M-TP', 'Nhạc Trẻ', 'Nguyễn Thanh Tùng', 233000),
        ('Hãy Trao Cho Anh', 'Chúng Ta Của Hiện Tại (Tuyển Tập)', 'Sơn Tùng M-TP', 'Nhạc Trẻ', 'Nguyễn Thanh Tùng', 245000),

        ('Mang Tiền Về Cho Mẹ', 'Show Của Đen', 'Đen Vâu', 'Rap Việt', 'Nguyễn Đức Cường', 302000),
        ('Đi Về Nhà', 'Show Của Đen', 'Đen Vâu', 'Rap Việt', 'Hứa Kim Tuyền, Đen Vâu', 214000),
        ('Bài Này Chill Phết', 'Show Của Đen', 'Đen Vâu', 'Rap Việt', 'Đen Vâu', 275000),
        ('Hai Triệu Năm', 'Show Của Đen', 'Đen Vâu', 'Rap Việt', 'Đen Vâu', 217000),

        ('Ước Gì', 'Tâm 9', 'Mỹ Tâm', 'Nhạc Trữ Tình', 'Võ Thiện Thanh', 298000),
        ('Họa Mi Tóc Nâu', 'Tâm 9', 'Mỹ Tâm', 'Nhạc Trẻ', 'Trần Huân', 242000),
        ('Đừng Hỏi Em', 'Tâm 9', 'Mỹ Tâm', 'Nhạc Trữ Tình', 'Mỹ Tâm', 265000),
        ('Người Hãy Quên Em Đi', 'Tâm 9', 'Mỹ Tâm', 'Nhạc Trẻ', 'Khắc Hưng', 238000),

        ('Tháng Tư Là Lời Nói Dối Của Em', 'Truyện Ngắn', 'Hà Anh Tuấn', 'Nhạc Trữ Tình', 'Phạm Toàn Thắng', 310000),
        ('Xuân Thì', 'Truyện Ngắn', 'Hà Anh Tuấn', 'Nhạc Trữ Tình', 'Phan Mạnh Quỳnh', 284000),
        ('Chuyện Của Mùa Đông', 'Truyện Ngắn', 'Hà Anh Tuấn', 'Nhạc Trữ Tình', 'Phạm Toàn Thắng', 268000),
        ('Tháng Mấy Em Nhớ Anh?', 'Truyện Ngắn', 'Hà Anh Tuấn', 'Nhạc Trữ Tình', 'Nguyễn Minh Cường', 295000),

        ('Để Mị Nói Cho Mà Nghe', 'Hoàng', 'Hoàng Thùy Linh', 'Nhạc Trẻ', 'Thịnh Kainz', 194000),
        ('See Tình', 'Hoàng', 'Hoàng Thùy Linh', 'Nhạc Trẻ', 'DTAP', 185000),
        ('Bánh Trôi Nước', 'Hoàng', 'Hoàng Thùy Linh', 'Nhạc Trẻ', 'Hồ Hoài Anh', 212000),
        ('Bo Xì Bo', 'Hoàng', 'Hoàng Thùy Linh', 'Nhạc Trẻ', 'DTAP', 201000),

        ('Lạ Lùng', 'Một Vạn Năm', 'Vũ.', 'Indie Việt', 'Thái Vũ', 261000),
        ('Bước Qua Nhau', 'Một Vạn Năm', 'Vũ.', 'Indie Việt', 'Thái Vũ', 257000),
        ('Bước Qua Mùa Cô Đơn', 'Một Vạn Năm', 'Vũ.', 'Indie Việt', 'Thái Vũ', 278000),
        ('Những Lời Hứa Bỏ Quên', 'Một Vạn Năm', 'Vũ.', 'Indie Việt', 'Thái Vũ', 249000)
) AS v(track_name, album_title, artist_name, genre_name, composer, duration_ms)
JOIN artist a ON a.name = v.artist_name
JOIN album al ON al.title = v.album_title AND al.artist_id = a.artist_id
JOIN genre g ON g.name = v.genre_name
CROSS JOIN (
    SELECT media_type_id FROM media_type ORDER BY media_type_id ASC LIMIT 1
) AS mt
WHERE NOT EXISTS (
    SELECT 1 FROM track t WHERE t.album_id = al.album_id AND t.name = v.track_name
);

-- 5. Re-synchronize sequences
SELECT setval(pg_get_serial_sequence('artist', 'artist_id'), COALESCE((SELECT MAX(artist_id) FROM artist), 1));
SELECT setval(pg_get_serial_sequence('album', 'album_id'), COALESCE((SELECT MAX(album_id) FROM album), 1));
SELECT setval(pg_get_serial_sequence('genre', 'genre_id'), COALESCE((SELECT MAX(genre_id) FROM genre), 1));
SELECT setval(pg_get_serial_sequence('track', 'track_id'), COALESCE((SELECT MAX(track_id) FROM track), 1));

COMMIT;
