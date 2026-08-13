"""
LEGACY / UNUSED -- kept for reference only.

WHAT THIS WAS: before the app was moved onto PostgreSQL (Neon), these
dictionaries WERE the database. The services read and wrote them in memory,
which is why they are keyed by id -- that made lookups instant, the same way a
primary key does in a real table.

WHY IT IS STILL HERE BUT NOT IMPORTED ANYWHERE:
every service now reads through app/data/database.py instead, so nothing in the
running app touches this file. It is left in the repo as a record of the
pre-database design.

WARNING -- DO NOT TRUST THESE VALUES:
they are a frozen snapshot and have already drifted from the real database. For
example branch 1 is called "Main Branch" here, while the actual branches table
says "Branch 1". Anyone reading this file to find out what is in the system will
be misled; query the database instead.

If you want this gone, deleting the file is safe -- a project-wide search shows
no module imports it.
"""

from datetime import datetime, timedelta

# timedelta backdates the created_at/timestamp fields so the seed data looks
# like it accumulated over the past year rather than all being created at once.
#sample data for branches
BRANCHES = {
    1: {
        "id": 1,
        "name": "Main Branch",
        "location": "123 Main St",
        "manager": "Tom Joe",
        "phone": "555-5555-0001"
    },
    2: {
        "id": 2,
        "name": "Branch 2",
        "location": "456 Birch Ave",
        "manager": "Sarah Jones",
        "phone": "555-5555-0002"
    },
    3: {
        "id": 3,
        "name": "Branch 3",
        "location": "789 Pine Rd",
        "manager": "Mike Newman",
        "phone": "555-5555-0003"
    }
}
 
#customers sample data 
CUSTOMERS = {
    1: {
        "id": 1,
        "name": "Ricky",
        "email": "ricky@example.com",
        "phone": "123-456-7890",
        "address": "100 Maple Dr",
        "branch_id": 1,
        "created_at": datetime.now() - timedelta(days=365),
        "is_active": True
    },
    2: {
        "id": 2,
        "name": "Ray",
        "email": "ray@example.com",
        "phone": "123-456-7891",
        "address": "200 Elm St",
        "branch_id": 1,
        "created_at": datetime.now() - timedelta(days=180),
        "is_active": True
    },
    3: {
        "id": 3,
        "name": "Santosh",
        "email": "santosh@example.com",
        "phone": "123-456-7892",
        "address": "300 Pine Ln",
        "branch_id": 2,
        "created_at": datetime.now() - timedelta(days=90),
        "is_active": True
    },
    4: {
        "id": 4,
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "phone": "555-1004",
        "address": "400 Cedar Blvd",
        "branch_id": 2,
        "created_at": datetime.now() - timedelta(days=60),
        "is_active": True
    },
    5: {
        "id": 5,
        "name": "Bob Wilson",
        "email": "bob@example.com",
        "phone": "555-1005",
        "address": "500 Birch Way",
        "branch_id": 3,
        "created_at": datetime.now() - timedelta(days=30),
        "is_active": True
    }
}

#sample data for accounts 
ACCOUNTS = {
    1: {
        "id": 1,
        "customer_id": 1,
        "account_type": "Checking",
        "balance": 2500.00,
        "branch_id": 1,
        "created_at": datetime.now() - timedelta(days=365),
        "is_active": True
    },
    2: {
        "id": 2,
        "customer_id": 1,
        "account_type": "Savings",
        "balance": 10000.00,
        "branch_id": 1,
        "created_at": datetime.now() - timedelta(days=360),
        "is_active": True
    },
    3: {
        "id": 3,
        "customer_id": 2,
        "account_type": "Checking",
        "balance": 1500.00,
        "branch_id": 1,
        "created_at": datetime.now() - timedelta(days=180),
        "is_active": True
    },
    4: {
        "id": 4,
        "customer_id": 2,
        "account_type": "Savings",
        "balance": 5000.00,
        "branch_id": 1,
        "created_at": datetime.now() - timedelta(days=175),
        "is_active": True
    },
    5: {
        "id": 5,
        "customer_id": 3,
        "account_type": "Checking",
        "balance": 3200.00,
        "branch_id": 2,
        "created_at": datetime.now() - timedelta(days=90),
        "is_active": True
    },
    6: {
        "id": 6,
        "customer_id": 4,
        "account_type": "Checking",
        "balance": 8500.00,
        "branch_id": 2,
        "created_at": datetime.now() - timedelta(days=60),
        "is_active": True
    },
    7: {
        "id": 7,
        "customer_id": 5,
        "account_type": "Checking",
        "balance": 500.00,
        "branch_id": 3,
        "created_at": datetime.now() - timedelta(days=30),
        "is_active": True
    }
}
 

#sample data for transactions
TRANSACTIONS = {
    1: {
        "id": 1,
        "from_account_id": 1,
        "to_account_id": 2,
        "amount": 500.00,
        "type": "TRANSFER",
        "timestamp": datetime.now() - timedelta(days=10),
        "status": "SUCCESS",
        "description": "Transfer to savings"
    },
    2: {
        "id": 2,
        "from_account_id": 1,
        "to_account_id": 3,
        "amount": 200.00,
        "type": "TRANSFER",
        "timestamp": datetime.now() - timedelta(days=7),
        "status": "SUCCESS",
        "description": "Payment to Ray"
    },
    3: {
        "id": 3,
        "from_account_id": 3,
        "to_account_id": 5,
        "amount": 100.00,
        "type": "TRANSFER",
        "timestamp": datetime.now() - timedelta(days=5),
        "status": "SUCCESS",
        "description": "Payment to Santosh"
    },
    4: {
        "id": 4,
        "from_account_id": 6,
        "to_account_id": 1,
        "amount": 1000.00,
        "type": "TRANSFER",
        "timestamp": datetime.now() - timedelta(days=3),
        "status": "SUCCESS",
        "description": "Refund from Alice"
    },
    5: {
        "id": 5,
        "from_account_id": 1,
        "to_account_id": 6,
        "amount": 50.00,
        "type": "TRANSFER",
        "timestamp": datetime.now() - timedelta(days=1),
        "status": "SUCCESS",
        "description": "Small payment"
    }
}