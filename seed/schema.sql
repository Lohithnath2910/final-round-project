-- Multi-tenant HMS schema. Every table carries property_id; scope ALL queries by it server-side.
CREATE TABLE IF NOT EXISTS properties (
  property_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  city TEXT,
  total_rooms INT,
  property_config JSONB
);
CREATE TABLE IF NOT EXISTS rooms (
  room_id TEXT PRIMARY KEY,
  property_id TEXT REFERENCES properties(property_id),
  room_type TEXT,            -- standard | deluxe | suite
  capacity INT
);
CREATE TABLE IF NOT EXISTS rates (
  rate_id TEXT PRIMARY KEY,
  property_id TEXT REFERENCES properties(property_id),
  room_type TEXT,
  date DATE,
  price_inr INT
);
CREATE TABLE IF NOT EXISTS bookings (
  booking_id TEXT PRIMARY KEY,
  property_id TEXT REFERENCES properties(property_id),
  room_type TEXT,
  checkin DATE,
  checkout DATE,
  status TEXT,               -- confirmed | cancelled | no_show | checked_out
  amount_inr INT,
  source TEXT                -- direct | mmt | booking_com | agoda
);


CREATE TABLE IF NOT EXISTS messages (
  message_id TEXT PRIMARY KEY,
  property_id TEXT REFERENCES properties(property_id),
  guest_id TEXT NOT NULL,
  text TEXT NOT NULL,
  intent TEXT,
  confidence FLOAT,
  status TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS messages_message_id_uidx ON messages(message_id);

CREATE TABLE IF NOT EXISTS events (
  event_id TEXT PRIMARY KEY,
  property_id TEXT REFERENCES properties(property_id),
  event_type TEXT NOT NULL,
  payload JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS workflow_jobs (
  job_id TEXT PRIMARY KEY,
  property_id TEXT REFERENCES properties(property_id),
  job_type TEXT NOT NULL,
  status TEXT,
  retry_count INT DEFAULT 0,
  payload JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);