DROP DATABASE IF EXISTS fire_detection_system;
CREATE DATABASE fire_detection_system;
USE fire_detection_system;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL
);
