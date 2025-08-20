-- User表
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    age INT,
    gender ENUM('M', 'F', 'Other'),
    height DECIMAL(5,2),
    weight DECIMAL(5,2),
    activity_level ENUM('Sedentary', 'Light', 'Moderate', 'Active', 'Very Active'),
    avatar VARCHAR(255) DEFAULT '&#x1F34E;',  -- 使用HTML实体编码存储emoji，默认为苹果emoji的编码
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 食物表
CREATE TABLE foods (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    calories_per_100g DECIMAL(6,2),
    protein_per_100g DECIMAL(5,2),
    carbs_per_100g DECIMAL(5,2),
    fat_per_100g DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 餐食记录表
CREATE TABLE meal_records (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    food_id INT,
    meal_type ENUM('Breakfast', 'Lunch', 'Dinner', 'Snack') NOT NULL,
    serving_size DECIMAL(6,2) NOT NULL,
    calories_consumed DECIMAL(6,2),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE SET NULL
);

-- 目标表
CREATE TABLE goals (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    goal_type ENUM('Weight Loss', 'Muscle Gain', 'Maintenance') NOT NULL,
    target_weight DECIMAL(5,2),
    target_date DATE,
    daily_calorie_goal DECIMAL(6,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 群组表
CREATE TABLE vgroups (
    id INT PRIMARY KEY AUTO_INCREMENT,
    group_name VARCHAR(100) NOT NULL,
    description TEXT,
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
);

-- 群组成员表
CREATE TABLE group_members (
    id INT PRIMARY KEY AUTO_INCREMENT,
    group_id INT NOT NULL,
    user_id INT NOT NULL,
    role ENUM('Admin', 'Member') DEFAULT 'Member',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES vgroups(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_group_user (group_id, user_id)
);

-- 群组挑战表
CREATE TABLE group_challenges (
    id INT PRIMARY KEY AUTO_INCREMENT,
    group_id INT NOT NULL,
    challenge_name VARCHAR(100) NOT NULL,
    description TEXT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    challenge_type ENUM('Calorie Intake', 'Exercise', 'Water Intake') NOT NULL,
    target_value DECIMAL(8,2),
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES vgroups(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
);

-- 挑战打卡记录表
CREATE TABLE challenge_checkins (
    id INT PRIMARY KEY AUTO_INCREMENT,
    participant_id INT NOT NULL,
    checkin_value DECIMAL(8,2) NOT NULL,
    note TEXT,
    checkin_date DATE DEFAULT (CURRENT_DATE),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (participant_id) REFERENCES challenge_participants(id) ON DELETE CASCADE
);

-- 群组活动表
CREATE TABLE group_activities (
    id INT PRIMARY KEY AUTO_INCREMENT,
    group_id INT NOT NULL,
    user_id INT NOT NULL,
    activity_type ENUM('Meal', 'Exercise', 'Water', 'Sleep') NOT NULL,
    record_id INT NOT NULL,
    shared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES vgroups(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 群组消息表
CREATE TABLE group_messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    group_id INT NOT NULL,
    user_id INT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES vgroups(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 健康挑战表
CREATE TABLE IF NOT EXISTS health_challenges (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    target_value DECIMAL(10,2) DEFAULT 0,
    unit VARCHAR(50) DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 用户参与挑战表
CREATE TABLE IF NOT EXISTS user_challenges (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    challenge_id INT NOT NULL,
    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    progress DECIMAL(10,2) DEFAULT 0,
    is_completed BOOLEAN DEFAULT FALSE,
    completed_date TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (challenge_id) REFERENCES health_challenges(id) ON DELETE CASCADE
);

-- 挑战打卡记录表
CREATE TABLE IF NOT EXISTS challenge_checkins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_challenge_id INT NOT NULL,
    checkin_date DATE NOT NULL,
    checkin_value DECIMAL(10,2) DEFAULT 0,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_challenge_id) REFERENCES user_challenges(id) ON DELETE CASCADE
);

-- 创建索引以提高查询性能
CREATE INDEX idx_meal_records_user_date ON meal_records(user_id, recorded_at);
CREATE INDEX idx_group_members_user ON group_members(user_id);
CREATE INDEX idx_group_challenges_group_date ON group_challenges(group_id, start_date);
CREATE INDEX idx_challenge_participants_challenge ON challenge_participants(challenge_id);
CREATE INDEX idx_group_activities_group_date ON group_activities(group_id, shared_at);
CREATE INDEX idx_group_messages_group_date ON group_messages(group_id, created_at);
CREATE INDEX idx_health_challenges_dates ON health_challenges(start_date, end_date);
CREATE INDEX idx_user_challenges_user_id ON user_challenges(user_id);
CREATE INDEX idx_user_challenges_challenge_id ON user_challenges(challenge_id);
CREATE INDEX idx_challenge_checkins_user_challenge_id ON challenge_checkins(user_challenge_id);
CREATE INDEX idx_challenge_checkins_date ON challenge_checkins(checkin_date);

-- 活动日记表
CREATE TABLE activity_diary (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    activity_type VARCHAR(100) NOT NULL,
    duration INT NOT NULL, -- 持续时间（分钟）
    calories_burned DECIMAL(6,2) NOT NULL, -- 消耗卡路里
    date DATE NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_date (user_id, date)
);