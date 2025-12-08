#!/bin/bash
#
# State Management Library
# Provides SQLite-based state tracking with passphrase-based encryption
#
# Usage:
#   source scripts/lib/state.sh
#   state_init
#   state_set "key" "value"
#   state_set "secret_key" "sensitive_value" --encrypt
#   value=$(state_get "key")
#   state_complete "step_name"
#   if state_check "step_name"; then echo "done"; fi
#

STATE_DIR="${STATE_DIR:-.state}"
STATE_DB="${STATE_DIR}/workflow.db"
STATE_PASS_CACHE=""

# Get passphrase (cached for session)
_state_get_passphrase() {
    if [[ -n "$STATE_PASS_CACHE" ]]; then
        echo "$STATE_PASS_CACHE"
        return
    fi
    
    # Check for password file
    if [[ -f "INSECURE_PASSWORD_TEXT" ]]; then
        STATE_PASS_CACHE=$(cat INSECURE_PASSWORD_TEXT | tr -d '\n')
        echo "$STATE_PASS_CACHE"
        return
    fi
    
    # Prompt user
    read -s -p "Enter state passphrase: " pass
    echo >&2
    STATE_PASS_CACHE="$pass"
    echo "$STATE_PASS_CACHE"
}

# Encrypt a value using openssl (cross-platform)
_state_encrypt() {
    local value="$1"
    local pass=$(_state_get_passphrase)
    echo -n "$value" | openssl enc -aes-256-cbc -pbkdf2 -iter 100000 -base64 -A -pass "pass:$pass" 2>/dev/null
}

# Decrypt a value using openssl (cross-platform)
_state_decrypt() {
    local encrypted="$1"
    local pass=$(_state_get_passphrase)
    echo -n "$encrypted" | openssl enc -aes-256-cbc -pbkdf2 -iter 100000 -d -base64 -A -pass "pass:$pass" 2>/dev/null
}

# Initialize state database
state_init() {
    mkdir -p "$STATE_DIR"
    chmod 700 "$STATE_DIR"
    
    sqlite3 "$STATE_DB" <<EOF
CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    encrypted INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS steps (
    name TEXT PRIMARY KEY,
    status TEXT DEFAULT 'pending',
    started_at TEXT,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT
);
EOF
    
    sqlite3 "$STATE_DB" "INSERT OR REPLACE INTO metadata (key, value) VALUES ('version', '1.0');"
}

# Set a config value
# Usage: state_set KEY VALUE [--encrypt]
state_set() {
    local key="$1"
    local value="$2"
    local encrypt=0
    
    if [[ "$3" == "--encrypt" ]]; then
        encrypt=1
        value=$(_state_encrypt "$value")
    fi
    
    sqlite3 "$STATE_DB" "INSERT OR REPLACE INTO config (key, value, encrypted, updated_at) VALUES ('$key', '$value', $encrypt, CURRENT_TIMESTAMP);"
}

# Get a config value
# Usage: state_get KEY
state_get() {
    local key="$1"
    local row=$(sqlite3 "$STATE_DB" "SELECT value, encrypted FROM config WHERE key='$key';")
    
    if [[ -z "$row" ]]; then
        return 1
    fi
    
    local value=$(echo "$row" | cut -d'|' -f1)
    local encrypted=$(echo "$row" | cut -d'|' -f2)
    
    if [[ "$encrypted" == "1" ]]; then
        _state_decrypt "$value"
    else
        echo "$value"
    fi
}

# Check if a step is completed
state_check() {
    local step="$1"
    local status=$(sqlite3 "$STATE_DB" "SELECT status FROM steps WHERE name='$step';")
    [[ "$status" == "completed" ]]
}

# Start a step
state_start() {
    local step="$1"
    sqlite3 "$STATE_DB" "INSERT OR REPLACE INTO steps (name, status, started_at) VALUES ('$step', 'in_progress', CURRENT_TIMESTAMP);"
}

# Complete a step
state_complete() {
    local step="$1"
    sqlite3 "$STATE_DB" "UPDATE steps SET status='completed', completed_at=CURRENT_TIMESTAMP WHERE name='$step';"
}

# Fail a step
state_fail() {
    local step="$1"
    sqlite3 "$STATE_DB" "UPDATE steps SET status='failed' WHERE name='$step';"
}

# Reset all state
state_reset() {
    rm -rf "$STATE_DIR"
    STATE_PASS_CACHE=""
    state_init
}

# Show current status
state_status() {
    echo "State Database: $STATE_DB"
    echo ""
    echo "Configuration:"
    sqlite3 -header -column "$STATE_DB" "SELECT key, CASE WHEN encrypted=1 THEN '***' ELSE value END as value FROM config;"
    echo ""
    echo "Steps:"
    sqlite3 -header -column "$STATE_DB" "SELECT name, status, completed_at FROM steps;"
}

# Export (non-encrypted only)
state_export() {
    echo "{"
    echo "  \"config\": {"
    sqlite3 "$STATE_DB" "SELECT '    \"' || key || '\": \"' || CASE WHEN encrypted=1 THEN '***' ELSE value END || '\",' FROM config;" | sed '$ s/,$//'
    echo "  },"
    echo "  \"steps\": {"
    sqlite3 "$STATE_DB" "SELECT '    \"' || name || '\": \"' || status || '\",' FROM steps;" | sed '$ s/,$//'
    echo "  }"
    echo "}"
}

# Auto-initialize if needed
if [[ ! -f "$STATE_DB" ]] && [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    state_init
fi
