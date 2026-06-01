-- seed_with_rls.sql
-- Run this script as a normal user after creating schema.sql which enables RLS.
-- It sets app.current_property per-tenant and inserts tenant rows so WITH CHECK passes.

-- Hotel A
SELECT set_config('app.current_property', 'hotel_a', false);

INSERT INTO properties(property_id, name, city, total_rooms)
VALUES
 ('hotel_a','Hotel Surya','Varanasi',24)
ON CONFLICT (property_id) DO NOTHING;

INSERT INTO rooms(room_id, property_id, room_type, capacity) VALUES
 ('a1','hotel_a','deluxe',2),('a2','hotel_a','standard',2),('a3','hotel_a','suite',3)
ON CONFLICT (room_id) DO NOTHING;

INSERT INTO rates(rate_id, property_id, room_type, date, price_inr) VALUES
 ('r1','hotel_a','deluxe','2026-05-30',3200),('r2','hotel_a','standard','2026-05-30',1800),
 ('r3','hotel_a','deluxe','2026-05-31',3600)
ON CONFLICT (rate_id) DO NOTHING;

INSERT INTO bookings(booking_id, property_id, room_type, checkin, checkout, status, amount_inr, source) VALUES
 ('bk1','hotel_a','deluxe','2026-05-02','2026-05-04','checked_out',6400,'mmt'),
 ('bk2','hotel_a','standard','2026-05-10','2026-05-11','confirmed',1800,'direct'),
 ('bk3','hotel_a','deluxe','2026-05-17','2026-05-18','no_show',3200,'booking_com'),
 ('bk4','hotel_a','suite','2026-05-24','2026-05-26','cancelled',8000,'agoda'),
 ('bk5','hotel_a','standard','2026-05-30','2026-05-31','confirmed',1800,'direct')
ON CONFLICT (booking_id) DO NOTHING;

-- Hotel B
SELECT set_config('app.current_property', 'hotel_b', false);

INSERT INTO properties(property_id, name, city, total_rooms)
VALUES
 ('hotel_b','Coastal Stay PG','Bengaluru',40)
ON CONFLICT (property_id) DO NOTHING;

INSERT INTO rooms(room_id, property_id, room_type, capacity) VALUES
 ('b1','hotel_b','standard',1),('b2','hotel_b','standard',2)
ON CONFLICT (room_id) DO NOTHING;

INSERT INTO rates(rate_id, property_id, room_type, date, price_inr) VALUES
 ('r4','hotel_b','standard','2026-05-30',900)
ON CONFLICT (rate_id) DO NOTHING;

INSERT INTO bookings(booking_id, property_id, room_type, checkin, checkout, status, amount_inr, source) VALUES
 ('bk6','hotel_b','standard','2026-05-03','2026-05-05','checked_out',1800,'direct'),
 ('bk7','hotel_b','standard','2026-05-30','2026-05-31','confirmed',900,'mmt')
ON CONFLICT (booking_id) DO NOTHING;

-- Clear session property after seeding
SELECT set_config('app.current_property', '', false);
