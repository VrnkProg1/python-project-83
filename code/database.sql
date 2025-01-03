CREATE TABLE urls (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at DATE
);

id, url_id, status_code, h1, title, description и created_at

CREATE TABLE url_checks (
    id SERIAL PRIMARY KEY,
    url_id INT,
    status_code INT,
    h1 VARCHAR(255),
    title VARCHAR(255),
    description VARCHAR(255),
    created_at DATE,
    FOREIGN KEY (url_id) REFERENCES urls(id)
);
