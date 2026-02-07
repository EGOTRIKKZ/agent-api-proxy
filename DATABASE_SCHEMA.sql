-- Agent API Proxy - Database Schema
-- SQLite Database Schema

-- API Keys Table
-- Stores API keys for authentication
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT UNIQUE NOT NULL,           -- Unique user identifier
    api_key TEXT UNIQUE NOT NULL,            -- API key (format: sk_xxxxx)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1,             -- 1 = active, 0 = inactive
    
    INDEX idx_api_key (api_key),
    INDEX idx_user_id (user_id)
);

-- Usage Logs Table
-- Tracks all API calls and costs
CREATE TABLE usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,                   -- References api_keys.user_id
    endpoint TEXT NOT NULL,                  -- API endpoint called
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    cost INTEGER NOT NULL,                   -- Cost in cents
    success INTEGER DEFAULT 1,               -- 1 = success, 0 = failure
    error_message TEXT,                      -- Error details (if failed)
    
    INDEX idx_user_id (user_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_endpoint (endpoint)
);

-- Example Queries
-- ===============

-- Create a new API key
INSERT INTO api_keys (user_id, api_key)
VALUES ('user123', 'sk_abc123xyz789');

-- Log an API call
INSERT INTO usage_logs (user_id, endpoint, cost, success)
VALUES ('user123', '/api/reddit/search', 5, 1);

-- Get user's total usage
SELECT 
    user_id,
    COUNT(*) as total_requests,
    SUM(cost) as total_cost_cents,
    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_requests,
    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed_requests
FROM usage_logs
WHERE user_id = 'user123'
GROUP BY user_id;

-- Get usage breakdown by endpoint
SELECT 
    endpoint,
    COUNT(*) as request_count,
    SUM(cost) as total_cost,
    AVG(cost) as avg_cost,
    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed
FROM usage_logs
WHERE user_id = 'user123'
    AND timestamp >= datetime('now', '-30 days')
GROUP BY endpoint;

-- Get recent activity
SELECT 
    endpoint,
    timestamp,
    cost,
    success,
    error_message
FROM usage_logs
WHERE user_id = 'user123'
ORDER BY timestamp DESC
LIMIT 50;

-- Get all active API keys
SELECT 
    user_id,
    api_key,
    created_at
FROM api_keys
WHERE is_active = 1;

-- Deactivate an API key
UPDATE api_keys
SET is_active = 0
WHERE user_id = 'user123';

-- Monthly usage statistics
SELECT 
    strftime('%Y-%m', timestamp) as month,
    COUNT(*) as total_requests,
    SUM(cost) as total_cost_cents,
    SUM(cost) / 100.0 as total_cost_dollars
FROM usage_logs
WHERE user_id = 'user123'
GROUP BY strftime('%Y-%m', timestamp)
ORDER BY month DESC;
