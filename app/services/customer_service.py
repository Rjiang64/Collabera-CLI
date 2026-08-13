"""Customer business logic -- now backed by PostgreSQL instead of in-memory dicts.

Every method uses the helpers from app.database:
  * query_all  -> SELECT returning many rows
  * query_one  -> SELECT returning one row (or None)
  * execute    -> INSERT/UPDATE/DELETE (commits automatically)

Rows come back as dicts (because of dict_row), so the return shape matches
what the controllers already expect -- customer["name"], etc.
"""
from app.data.database import execute, query_all, query_one


class CustomerService:
    def create_customer(self, name, email, phone, address, branch_id):
        # RETURNING * hands back the full new row (with its generated id) in one trip.
        return execute(
            """
            INSERT INTO customers (name, email, phone, address, branch_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *;
            """,
            (name, email, phone, address, branch_id),
        )

    def get_all_customers(self):
        return query_all("SELECT * FROM customers ORDER BY id;")

    def get_customer(self, customer_id):
        return query_one("SELECT * FROM customers WHERE id = %s;", (customer_id,))

    def update_customer(self, customer_id, updates: dict):
        if not updates:
            return self.get_customer(customer_id)
        # build "col = %s" pairs dynamically from whatever fields were sent
        columns = ", ".join(f"{key} = %s" for key in updates)
        values = list(updates.values()) + [customer_id]
        return execute(
            f"UPDATE customers SET {columns} WHERE id = %s RETURNING *;",
            values,
        )

    def deactivate_customer(self, customer_id):
        return execute(
            "UPDATE customers SET is_active = FALSE WHERE id = %s RETURNING *;",
            (customer_id,),
        )