CREATE DATABASE IF NOT EXISTS scrum_team_12;
USE scrum_team_12;

-- -----------------------------
--   RESERVATIONS TABLE
-- -----------------------------
CREATE TABLE IF NOT EXISTS reservations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    passenger_name VARCHAR(100) NOT NULL,
    passenger_email VARCHAR(100) NOT NULL,
    flight_number VARCHAR(50) NOT NULL,
    seat_number VARCHAR(10),
    price DECIMAL(10,2) NOT NULL,
    reservation_code VARCHAR(20) UNIQUE NOT NULL,
    reservation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------
--   ADMIN USERS TABLE
-- -----------------------------
CREATE TABLE IF NOT EXISTS admin_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL
);

-- Creates a default admin login for testing:
INSERT INTO admin_users (username, password_hash)
VALUES ('admin', 'admin123') 
ON DUPLICATE KEY UPDATE username=username;
