import random
import numpy as np
import psycopg2
from faker import Faker
from datetime import datetime, timedelta
from decimal import Decimal
import hashlib

faker = Faker()

# Database connection settings
DATABASES = {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': 'ethio_stock_simulation_db',
    'USER': 'stock_user',
    'PASSWORD': 'Amen@2461',
    'HOST': 'localhost',
    'PORT': '5432',
}
# List of Ethiopian companies and sectors
ethiopian_companies = [
    ("Ethio Telecom", "Telecommunications"),
    ("Ethiopian Sugar Corporation", "Agriculture"),
    ("Commercial Bank of Ethiopia", "Banking"),
    ("Awash Bank", "Banking"),
    ("Dashen Bank", "Banking"),
    ("Bank of Abyssinia", "Banking"),
    ("Wegagen Bank", "Banking"),
    ("Nib International Bank", "Banking"),
    ("Berhan International Bank", "Banking"),
    ("Ethiopian Airlines", "Airlines"),
    ("Habesha Breweries", "Breweries"),
    ("Meta Brewery", "Breweries"),
    ("Ethiopian Shipping Lines", "Shipping"),
    ("MIDROC Ethiopia", "Manufacturing"),
    ("Anbessa City Bus", "Transport"),
    ("Ethiopian Electric Power", "Energy"),
    ("Amhara Bank", "Banking"),
    ("Enat Bank", "Banking"),
    ("Bunna Insurance", "Insurance"),
    ("Ethio Cement", "Manufacturing")
]

# Connect to the database
def connect_to_db():
    conn = psycopg2.connect(
        dbname=DATABASES['NAME'],
        user=DATABASES['USER'],
        password=DATABASES['PASSWORD'],
        host=DATABASES['HOST'],
        port=DATABASES['PORT']
    )
    return conn

# Generate and insert companies and stocks
def generate_and_insert_companies_and_stocks(conn):
    cursor = conn.cursor()

    # Fetch existing companies to avoid duplication
    cursor.execute("SELECT company_name FROM stocks_listedcompany;")
    existing_companies = {row[0] for row in cursor.fetchall()}

    # Fetch existing ticker symbols
    cursor.execute("SELECT ticker_symbol FROM stocks_stocks;")
    existing_ticker_symbols = {row[0] for row in cursor.fetchall()}

    for company_name, sector in ethiopian_companies:
        if company_name in existing_companies:
            continue  # Skip if the company already exists

        # Generate unique ticker symbol
        base_ticker_symbol = "".join([word[0] for word in company_name.split()])[:4].upper()
        ticker_symbol = base_ticker_symbol
        counter = 1
        while ticker_symbol in existing_ticker_symbols:
            ticker_symbol = f"{base_ticker_symbol}{counter}"
            counter += 1
        existing_ticker_symbols.add(ticker_symbol)

        total_shares = int(np.random.normal(loc=5000000, scale=1000000))
        current_price = round(np.random.normal(loc=1500, scale=200), 2)
        available_shares = int(total_shares * 0.8)
        max_trader_buy_limit = random.randint(1000, 10000)

        # Insert into ListedCompany table
        cursor.execute("""
            INSERT INTO stocks_listedcompany (company_name, sector, last_updated)
            VALUES (%s, %s, NOW())
            RETURNING id;
        """, (company_name, sector))
        company_id = cursor.fetchone()[0]

        # Insert into Stocks table
        cursor.execute("""
            INSERT INTO stocks_stocks (company_id, ticker_symbol, total_shares, available_shares, 
                                       current_price, max_trader_buy_limit, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW());
        """, (company_id, ticker_symbol, total_shares, available_shares, current_price, max_trader_buy_limit))

    conn.commit()
    print("Companies and Stocks inserted successfully.")
    cursor.close()

# Generate and insert users
def generate_and_insert_orders_and_trades(conn, num_orders_per_user=5):
    cursor = conn.cursor()

    # Fetch traders and stocks
    cursor.execute("SELECT id FROM users_customuser WHERE role = 'trader' AND kyc_verified = TRUE AND is_approved = TRUE;")
    traders = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT id, current_price, ticker_symbol, available_shares, max_trader_buy_limit FROM stocks_stocks;")
    stocks = cursor.fetchall()

    for trader_id in traders:
        for _ in range(num_orders_per_user):
            stock = random.choice(stocks)
            stock_id = stock[0]
            current_price = stock[1]
            ticker_symbol = stock[2]
            available_shares = stock[3]
            max_trader_buy_limit = stock[4]

            # Randomly choose between Buy or Sell
            action = random.choice(["Buy", "Sell"])

            quantity = random.randint(1, 50)

            # Ensure price calculations use Decimal
            random_factor = Decimal(str(np.random.uniform(-0.05, 0.05)))  # Convert float to Decimal
            price = round(current_price * (1 + random_factor), 2)

            # Ensure rules are followed
            if action == "Buy":
                # Skip if quantity exceeds max_trader_buy_limit or available shares
                cursor.execute("""
                    SELECT COALESCE(SUM(quantity), 0) FROM stocks_trade
                    WHERE user_id = %s AND stock_id = %s;
                """, (trader_id, stock_id))
                total_bought = cursor.fetchone()[0]

                if total_bought + quantity > max_trader_buy_limit or available_shares < quantity:
                    continue

                # Update available shares
                new_available_shares = available_shares - quantity
                cursor.execute("UPDATE stocks_stocks SET available_shares = %s WHERE id = %s;", (new_available_shares, stock_id))

                # Update portfolio
                cursor.execute("""
                    INSERT INTO stocks_usersportfolio (user_id, quantity, average_purchase_price, total_investment)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE
                    SET quantity = stocks_usersportfolio.quantity + %s,
                        total_investment = stocks_usersportfolio.total_investment + %s,
                        average_purchase_price = (stocks_usersportfolio.total_investment + %s) / (stocks_usersportfolio.quantity + %s);
                """, (trader_id, quantity, price * quantity, price * quantity, quantity, price * quantity, price * quantity, quantity))

            elif action == "Sell":
                # Skip if user doesn't have enough shares
                cursor.execute("""
                    SELECT quantity FROM stocks_usersportfolio WHERE user_id = %s;
                """, (trader_id,))
                portfolio_quantity = cursor.fetchone()[0] or 0

                if portfolio_quantity < quantity:
                    continue

                # Update portfolio
                cursor.execute("""
                    UPDATE stocks_usersportfolio
                    SET quantity = quantity - %s,
                        total_investment = total_investment - (average_purchase_price * %s)
                    WHERE user_id = %s;
                """, (quantity, quantity, trader_id))

            # Insert order
            cursor.execute("""
                INSERT INTO stocks_orders (user_id, stock_id, stock_symbol, order_type, action, price, quantity, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW());
            """, (trader_id, stock_id, ticker_symbol, "Market", action, price, quantity, "Fully Completed"))

            # Insert trade
            cursor.execute("""
                INSERT INTO stocks_trade (user_id, stock_id, quantity, price, trade_time)
                VALUES (%s, %s, %s, %s, NOW());
            """, (trader_id, stock_id, quantity, price))

    conn.commit()
    print("Orders and Trades inserted successfully.")
    cursor.close()



# Generate and insert orders and trades

def generate_and_insert_orders_and_trades(conn, num_orders_per_user=5):
    cursor = conn.cursor()

    # Fetch traders and stocks
    cursor.execute("SELECT id FROM users_customuser WHERE role = 'trader' AND kyc_verified = TRUE AND is_approved = TRUE;")
    traders = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT id, current_price, ticker_symbol, available_shares, max_trader_buy_limit FROM stocks_stocks;")
    stocks = cursor.fetchall()

    for trader_id in traders:
        for _ in range(num_orders_per_user):
            stock = random.choice(stocks)
            stock_id = stock[0]
            current_price = Decimal(stock[1])  # Ensure current_price is Decimal
            ticker_symbol = stock[2]
            available_shares = stock[3]
            max_trader_buy_limit = stock[4]

            # Randomly choose between Buy or Sell
            action = random.choice(["Buy", "Sell"])

            quantity = random.randint(1, 50)

            # Ensure price calculations use Decimal
            random_factor = Decimal(str(np.random.uniform(-0.05, 0.05)))  # Convert float to Decimal
            price = round(current_price * (1 + random_factor), 2)

            # Ensure rules are followed
            if action == "Buy":
                # Skip if quantity exceeds max_trader_buy_limit or available shares
                cursor.execute("""
                    SELECT COALESCE(SUM(quantity), 0) FROM stocks_trade
                    WHERE user_id = %s AND stock_id = %s;
                """, (trader_id, stock_id))
                total_bought = cursor.fetchone()[0]

                if total_bought + quantity > max_trader_buy_limit or available_shares < quantity:
                    continue

                # Update available shares
                new_available_shares = available_shares - quantity
                cursor.execute("UPDATE stocks_stocks SET available_shares = %s WHERE id = %s;", (new_available_shares, stock_id))

                # Update portfolio
                cursor.execute("""
                    INSERT INTO stocks_usersportfolio (user_id, quantity, average_purchase_price, total_investment)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE
                    SET quantity = stocks_usersportfolio.quantity + %s,
                        total_investment = stocks_usersportfolio.total_investment + %s,
                        average_purchase_price = (stocks_usersportfolio.total_investment + %s) / (stocks_usersportfolio.quantity + %s);
                """, (trader_id, quantity, price * quantity, price * quantity, quantity, price * quantity, price * quantity, quantity))

            elif action == "Sell":
                # Skip if user doesn't have enough shares
                cursor.execute("""
                    SELECT quantity FROM stocks_usersportfolio WHERE user_id = %s;
                """, (trader_id,))
                portfolio_quantity = cursor.fetchone()[0] or 0

                if portfolio_quantity < quantity:
                    continue

                # Update portfolio
                cursor.execute("""
                    UPDATE stocks_usersportfolio
                    SET quantity = quantity - %s,
                        total_investment = total_investment - (average_purchase_price * %s)
                    WHERE user_id = %s;
                """, (quantity, quantity, trader_id))

            # Insert order
            cursor.execute("""
                INSERT INTO stocks_orders (user_id, stock_id, stock_symbol, order_type, action, price, quantity, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW());
            """, (trader_id, stock_id, ticker_symbol, "Market", action, price, quantity, "Fully Completed"))

            # Insert trade
            cursor.execute("""
                INSERT INTO stocks_trade (user_id, stock_id, quantity, price, trade_time)
                VALUES (%s, %s, %s, %s, NOW());
            """, (trader_id, stock_id, quantity, price))

    conn.commit()
    print("Orders and Trades inserted successfully.")
    cursor.close()

# Main function to generate and insert data
def generate_and_insert_data():
    conn = connect_to_db()

    try:
        generate_and_insert_companies_and_stocks(conn)
        generate_and_insert_orders_and_trades(conn)
    finally:
        conn.close()

# Execute script
generate_and_insert_data()
