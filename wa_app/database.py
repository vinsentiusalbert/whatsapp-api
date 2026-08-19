import pymysql

from wa_app.config import settings


def get_db():
    return pymysql.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def ensure_tables() -> None:
    connection = get_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS whatsapp_messages (
                    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                    direction ENUM('INBOUND', 'OUTBOUND') NOT NULL,
                    message_id VARCHAR(255) NULL,
                    sender VARCHAR(100) NULL,
                    receiver VARCHAR(100) NULL,
                    sender_name VARCHAR(255) NULL,
                    message_type VARCHAR(50) DEFAULT 'text',
                    message TEXT NULL,
                    status VARCHAR(50) NULL,
                    http_status INT NULL,
                    raw_payload LONGTEXT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    KEY idx_direction (direction),
                    KEY idx_sender (sender),
                    KEY idx_receiver (receiver),
                    KEY idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS myads_campaign_sessions (
                    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                    phone VARCHAR(30) NOT NULL,
                    status VARCHAR(30) NOT NULL DEFAULT 'WAITING_FORM',
                    campaign_payload LONGTEXT NULL,
                    last_error TEXT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY uq_myads_campaign_phone (phone)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
    finally:
        connection.close()
