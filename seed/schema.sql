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

ALTER TABLE rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE rates ENABLE ROW LEVEL SECURITY;
ALTER TABLE bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE properties ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS properties_tenant_policy ON properties;
DROP POLICY IF EXISTS rooms_tenant_policy ON rooms;
DROP POLICY IF EXISTS rates_tenant_policy ON rates;
DROP POLICY IF EXISTS bookings_tenant_policy ON bookings;
DROP POLICY IF EXISTS messages_tenant_policy ON messages;
DROP POLICY IF EXISTS events_tenant_policy ON events;
DROP POLICY IF EXISTS workflow_jobs_tenant_policy ON workflow_jobs;


CREATE POLICY properties_tenant_policy
ON properties
FOR ALL
USING (
    property_id =
    current_setting(
        'app.current_property',
        true
    )
)
WITH CHECK (
    property_id =
    current_setting(
        'app.current_property',
        true
    )
);

-- =====================================================
-- ROOMS
-- =====================================================

CREATE POLICY rooms_tenant_policy
ON rooms
FOR ALL
USING (
    property_id =
    current_setting(
        'app.current_property',
        true
    )
)
WITH CHECK (
    property_id =
    current_setting(
        'app.current_property',
        true
    )
);

-- =====================================================
-- RATES
-- =====================================================

CREATE POLICY rates_tenant_policy
ON rates
FOR ALL
USING (
    property_id =
    current_setting(
        'app.current_property',
        true
    )
)
WITH CHECK (
    property_id =
    current_setting(
        'app.current_property',
        true
    )
);

-- =====================================================
-- BOOKINGS
-- =====================================================

CREATE POLICY bookings_tenant_policy
ON bookings
FOR ALL
USING (
    property_id =
    current_setting(
        'app.current_property',
        true
    )
)
WITH CHECK (
    property_id =
    current_setting(
        'app.current_property',
        true
    )
);

-- =====================================================
-- MESSAGES
-- =====================================================

CREATE POLICY messages_tenant_policy
ON messages
FOR ALL
USING (
    property_id =
    current_setting(
        'app.current_property',
        true
    )
)
WITH CHECK (
    property_id =
    current_setting(
        'app.current_property',
        true
    )
);

-- =====================================================
-- EVENTS
-- =====================================================

CREATE POLICY events_tenant_policy
ON events
FOR ALL
USING (
    property_id =
    current_setting(
        'app.current_property',
        true
    )
)
WITH CHECK (
    property_id =
    current_setting(
        'app.current_property',
        true
    )
);

-- =====================================================
-- WORKFLOW JOBS
-- =====================================================

CREATE POLICY workflow_jobs_tenant_policy
ON workflow_jobs
FOR ALL
USING (
    property_id =
    current_setting(
        'app.current_property',
        true
    )
)
WITH CHECK (
    property_id =
    current_setting(
        'app.current_property',
        true
    )
);