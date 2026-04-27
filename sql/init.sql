-- ============================================
-- 票务监控提醒系统 - MySQL 数据库初始化脚本
-- ============================================

-- 创建数据库（使用 utf8mb4 字符集以支持 emoji 等特殊字符）
CREATE DATABASE IF NOT EXISTS ticket_monitor
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE ticket_monitor;

-- ============================================
-- 用户表 - 存储注册用户信息
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id          INT          NOT NULL AUTO_INCREMENT COMMENT '用户ID，主键自增',
    username    VARCHAR(50)  NOT NULL                COMMENT '用户名，唯一',
    email       VARCHAR(100) NOT NULL                COMMENT '邮箱地址，唯一',
    hashed_password VARCHAR(200) NOT NULL            COMMENT '哈希后的密码',
    fcm_token   VARCHAR(500) NULL     DEFAULT NULL   COMMENT 'Firebase Cloud Messaging 推送令牌',
    email_notify_enabled     TINYINT(1) DEFAULT 1    COMMENT '是否启用邮件通知：1-启用 0-禁用',
    websocket_notify_enabled TINYINT(1) DEFAULT 1    COMMENT '是否启用 WebSocket 通知：1-启用 0-禁用',
    created_at  DATETIME     NULL     DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    PRIMARY KEY (id),
    UNIQUE INDEX uk_username (username),
    UNIQUE INDEX uk_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ============================================
-- 监控任务表 - 存储用户创建的票务监控任务
-- ============================================
CREATE TABLE IF NOT EXISTS monitor_tasks (
    id              INT          NOT NULL AUTO_INCREMENT COMMENT '任务ID，主键自增',
    user_id         INT          NOT NULL                COMMENT '所属用户ID',
    platform        VARCHAR(50)  NOT NULL                COMMENT '平台名称：damai/maoyan/funwandao',
    event_url       VARCHAR(500) NOT NULL                COMMENT '活动页面 URL',
    event_name      VARCHAR(200) NOT NULL                COMMENT '活动/演出名称',
    target_session  VARCHAR(200) NULL     DEFAULT NULL   COMMENT '目标场次（可选）',
    check_interval  INT          NULL     DEFAULT 30     COMMENT '检查间隔（秒）',
    is_active       TINYINT(1)   NULL     DEFAULT 1      COMMENT '是否启用：1-启用 0-停用',
    created_at      DATETIME     NULL     DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    PRIMARY KEY (id),
    INDEX idx_user_id (user_id),
    INDEX idx_platform (platform),
    CONSTRAINT fk_monitor_tasks_user_id
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='监控任务表';

-- ============================================
-- 票务状态快照表 - 存储每次检查的票务状态快照
-- ============================================
CREATE TABLE IF NOT EXISTS ticket_statuses (
    id          INT      NOT NULL AUTO_INCREMENT COMMENT '状态记录ID，主键自增',
    task_id     INT      NOT NULL                COMMENT '所属监控任务ID',
    status_data TEXT     NULL                     COMMENT '票务状态详情，JSON 格式字符串',
    checked_at  DATETIME NULL     DEFAULT CURRENT_TIMESTAMP COMMENT '检查时间',

    PRIMARY KEY (id),
    INDEX idx_task_id (task_id),
    INDEX idx_checked_at (checked_at),
    CONSTRAINT fk_ticket_statuses_task_id
        FOREIGN KEY (task_id) REFERENCES monitor_tasks (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='票务状态快照表';

-- ============================================
-- 通知记录表 - 存储发送给用户的所有通知记录
-- ============================================
CREATE TABLE IF NOT EXISTS notifications (
    id         INT         NOT NULL AUTO_INCREMENT COMMENT '通知ID，主键自增',
    user_id    INT         NOT NULL                COMMENT '接收通知的用户ID',
    task_id    INT         NULL     DEFAULT NULL   COMMENT '关联的监控任务ID（可为空）',
    message    TEXT        NOT NULL                COMMENT '通知内容',
    type       VARCHAR(20) NOT NULL                COMMENT '通知类型：websocket/email/fcm',
    is_read    TINYINT(1)  NULL     DEFAULT 0      COMMENT '是否已读：1-已读 0-未读',
    created_at DATETIME    NULL     DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    PRIMARY KEY (id),
    INDEX idx_user_id (user_id),
    INDEX idx_task_id (task_id),
    INDEX idx_type (type),
    INDEX idx_is_read (is_read),
    CONSTRAINT fk_notifications_user_id
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_notifications_task_id
        FOREIGN KEY (task_id) REFERENCES monitor_tasks (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通知记录表';
