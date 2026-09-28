-- Missing tables only; existing records and tables are preserved.
CREATE TABLE IF NOT EXISTS users (
 user_id INT PRIMARY KEY AUTO_INCREMENT, full_name VARCHAR(100) NOT NULL,
 email VARCHAR(100) NOT NULL UNIQUE, password VARCHAR(255) NOT NULL, phone VARCHAR(20),
 role ENUM('customer','admin') DEFAULT 'customer', status ENUM('active','inactive') DEFAULT 'active',
 created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS categories (
 category_id INT PRIMARY KEY AUTO_INCREMENT, category_name VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS products (
 product_id INT PRIMARY KEY AUTO_INCREMENT, category_id INT,
 product_name VARCHAR(100) NOT NULL, description VARCHAR(255), price DECIMAL(10,2) NOT NULL,
 image_path VARCHAR(255), availability BOOLEAN DEFAULT TRUE,
 FOREIGN KEY(category_id) REFERENCES categories(category_id)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS ingredients (
 ingredient_id INT PRIMARY KEY AUTO_INCREMENT, ingredient_name VARCHAR(100) NOT NULL,
 quantity DECIMAL(10,2) DEFAULT 0, unit VARCHAR(30) NOT NULL, reorder_level DECIMAL(10,2) DEFAULT 0
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS product_ingredients (
 product_id INT NOT NULL, ingredient_id INT NOT NULL, quantity_required DECIMAL(10,2) NOT NULL,
 PRIMARY KEY(product_id,ingredient_id), FOREIGN KEY(product_id) REFERENCES products(product_id),
 FOREIGN KEY(ingredient_id) REFERENCES ingredients(ingredient_id)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS orders (
 order_id INT PRIMARY KEY AUTO_INCREMENT, user_id INT NOT NULL,
 order_date DATETIME DEFAULT CURRENT_TIMESTAMP, total_amount DECIMAL(10,2) NOT NULL,
 status ENUM('Pending','Confirmed','Preparing','Ready','Completed','Cancelled') DEFAULT 'Pending',
 FOREIGN KEY(user_id) REFERENCES users(user_id)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS order_items (
 order_item_id INT PRIMARY KEY AUTO_INCREMENT, order_id INT NOT NULL, product_id INT NOT NULL,
 quantity INT NOT NULL, unit_price DECIMAL(10,2) NOT NULL, subtotal DECIMAL(10,2) NOT NULL,
 FOREIGN KEY(order_id) REFERENCES orders(order_id), FOREIGN KEY(product_id) REFERENCES products(product_id)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS payments (
 payment_id INT PRIMARY KEY AUTO_INCREMENT, order_id INT NOT NULL UNIQUE,
 payment_method ENUM('Cash','GCash') NOT NULL, amount_paid DECIMAL(10,2) NOT NULL,
 payment_status ENUM('Unpaid','Paid','Refunded') DEFAULT 'Unpaid', reference_number VARCHAR(100),
 payment_date DATETIME, FOREIGN KEY(order_id) REFERENCES orders(order_id)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS inventory_transactions (
 transaction_id INT PRIMARY KEY AUTO_INCREMENT, ingredient_id INT NOT NULL,
 transaction_type ENUM('Stock In','Stock Out','Adjustment'), quantity DECIMAL(10,2) NOT NULL,
 remarks VARCHAR(255), transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(ingredient_id) REFERENCES ingredients(ingredient_id)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS app_mutex (lock_id INT PRIMARY KEY) ENGINE=InnoDB;
INSERT IGNORE INTO app_mutex(lock_id) VALUES(1);
CREATE TABLE IF NOT EXISTS order_stock (
 order_id INT NOT NULL, ingredient_id INT NOT NULL, quantity DECIMAL(10,2) NOT NULL,
 PRIMARY KEY(order_id,ingredient_id), FOREIGN KEY(order_id) REFERENCES orders(order_id),
 FOREIGN KEY(ingredient_id) REFERENCES ingredients(ingredient_id)
) ENGINE=InnoDB;

