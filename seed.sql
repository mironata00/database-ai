-- =============================================================================
-- Database AI - Seed Data (Тестовые данные)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Create ENUM types
-- -----------------------------------------------------------------------------

DROP TYPE IF EXISTS user_role CASCADE;
CREATE TYPE user_role AS ENUM ('admin', 'manager', 'viewer');

DROP TYPE IF EXISTS supplierstatus CASCADE;
CREATE TYPE supplierstatus AS ENUM ('ACTIVE', 'PENDING', 'BLACKLIST', 'INACTIVE');

-- -----------------------------------------------------------------------------
-- 2. Create Tables
-- -----------------------------------------------------------------------------

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role user_role NOT NULL DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Suppliers table
CREATE TABLE IF NOT EXISTS suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(500) NOT NULL,
    inn VARCHAR(12) UNIQUE NOT NULL,
    kpp VARCHAR(9),
    ogrn VARCHAR(15),
    legal_address TEXT,
    actual_address TEXT,
    email VARCHAR(255),
    phone VARCHAR(50),
    website VARCHAR(500),
    contact_person VARCHAR(255),
    contact_position VARCHAR(255),
    contact_phone VARCHAR(50),
    contact_email VARCHAR(255),
    status supplierstatus DEFAULT 'ACTIVE'::supplierstatus,
    delivery_regions TEXT[],
    payment_terms TEXT,
    min_order_sum DECIMAL(12,2),
    rating FLOAT DEFAULT 0.0,
    is_blacklisted BOOLEAN DEFAULT false,
    blacklist_reason TEXT,
    raw_data_url VARCHAR(1000),
    tags_array TEXT[],
    last_email_sent_at TIMESTAMP,
    email_thread_id VARCHAR(255),
    import_source VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP
);

-- Audit logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id VARCHAR(100),
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent VARCHAR(500),
    endpoint VARCHAR(500),
    description TEXT,
    extra_metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_id UUID REFERENCES suppliers(id) ON DELETE CASCADE,
    sku VARCHAR(255) NOT NULL,
    name VARCHAR(1000) NOT NULL,
    brand VARCHAR(255),
    category VARCHAR(255),
    price DECIMAL(12,2),
    unit VARCHAR(50),
    stock INTEGER,
    tags TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(supplier_id, sku)
);

-- Campaigns table
CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    body TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'draft',
    scheduled_at TIMESTAMP,
    sent_at TIMESTAMP,
    total_recipients INTEGER DEFAULT 0,
    total_sent INTEGER DEFAULT 0,
    total_failed INTEGER DEFAULT 0,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- 3. Insert Test Data
-- -----------------------------------------------------------------------------

-- Insert test users
-- Пароль для обоих: admin123 и manager123
-- Хеши bcrypt с cost=12
INSERT INTO users (id, email, hashed_password, full_name, role, is_active)
VALUES 
    (gen_random_uuid(), 'admin@company.ru', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLRGhTqW', 'Алексей Иванов (Админ)', 'admin', true),
    (gen_random_uuid(), 'manager@company.ru', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLRGhTqW', 'Мария Петрова (Менеджер)', 'manager', true)
ON CONFLICT (email) DO UPDATE SET
    hashed_password = EXCLUDED.hashed_password,
    full_name = EXCLUDED.full_name,
    role = EXCLUDED.role;

-- Insert test suppliers
INSERT INTO suppliers (name, inn, email, phone, rating, is_blacklisted, blacklist_reason, status, tags_array) VALUES
    ('СтройКомплект', '7701234567', 'info@stroykomplekt.ru', '+7 (495) 123-45-67', 4.3, false, NULL, 'ACTIVE'::supplierstatus, ARRAY['Цемент', 'Knauf', 'Сухие смеси', 'Бетон']),
    ('ЭлектроМир', '7709876543', 'sales@electromir.ru', '+7 (495) 765-43-21', 4.3, false, NULL, 'ACTIVE'::supplierstatus, ARRAY['ABB', 'Schneider', 'Кабель', 'Розетки', 'Электрика']),
    ('Рога и Копыта', '7700000000', 'scam@example.com', NULL, 1.0, true, 'Мошенничество, не доставили товар', 'BLACKLIST'::supplierstatus, ARRAY['Воздух']),
    ('ООО "Стройматериалы"', '7724422835', 'simon-15@list.ru', '+7 (495) 888-99-00', 0.0, false, NULL, 'PENDING'::supplierstatus, ARRAY['Заявка на проверку', 'Новый поставщик'])
ON CONFLICT (inn) DO UPDATE SET
    rating = EXCLUDED.rating,
    is_blacklisted = EXCLUDED.is_blacklisted,
    status = EXCLUDED.status,
    tags_array = EXCLUDED.tags_array,
    blacklist_reason = EXCLUDED.blacklist_reason;

-- -----------------------------------------------------------------------------
-- 4. Create Indexes
-- -----------------------------------------------------------------------------

-- Users indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- Suppliers indexes
CREATE INDEX IF NOT EXISTS idx_suppliers_inn ON suppliers(inn);
CREATE INDEX IF NOT EXISTS idx_suppliers_name ON suppliers(name);
CREATE INDEX IF NOT EXISTS idx_suppliers_email ON suppliers(email);
CREATE INDEX IF NOT EXISTS idx_suppliers_status ON suppliers(status);
CREATE INDEX IF NOT EXISTS idx_suppliers_is_blacklisted ON suppliers(is_blacklisted);
CREATE INDEX IF NOT EXISTS idx_suppliers_rating ON suppliers(rating);
CREATE INDEX IF NOT EXISTS idx_suppliers_tags ON suppliers USING GIN(tags_array);
CREATE INDEX IF NOT EXISTS idx_suppliers_created_at ON suppliers(created_at);

-- Products indexes
CREATE INDEX IF NOT EXISTS idx_products_supplier_id ON products(supplier_id);
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_tags ON products USING GIN(tags);

-- Audit logs indexes
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity_type ON audit_logs(entity_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

-- Campaigns indexes
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaigns_created_by ON campaigns(created_by);
CREATE INDEX IF NOT EXISTS idx_campaigns_scheduled_at ON campaigns(scheduled_at);

-- -----------------------------------------------------------------------------
-- Success message
-- -----------------------------------------------------------------------------

SELECT 
    'Database initialized successfully!' as status,
    (SELECT COUNT(*) FROM users) as users_count,
    (SELECT COUNT(*) FROM suppliers) as suppliers_count;
