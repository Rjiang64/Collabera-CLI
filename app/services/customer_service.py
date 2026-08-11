"""
Customer business logic - now backed by PostgreSQL (Neon) instead of
in-memory sample data. Methods still return plain dicts, so the
controllers and Pydantic models did not have to change.
"""

from app.data.database import execute, query_all, query_one

# columns a client is allowed to change via update
_UPDATABLE = {"name", "email", "phone", "address", "branch_id", "is_active"}


class CustomerService:

    # CREATE
    def create_customer(self, name, email, phone, address, branch_id=1):
        return execute(
            """
            INSERT INTO customers (name, email, phone, address, branch_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
            """,
            (name, email, phone, address, branch_id),
        )

    # READ
    def get_all_customers(self):
        return query_all("SELECT * FROM customers ORDER BY id")

    def get_customer(self, customer_id):
        return query_one("SELECT * FROM customers WHERE id = %s", (customer_id,))

    # UPDATE
    def update_customer(self, customer_id, updates):
        # keep only real, allowed columns
        fields = {k: v for k, v in updates.items() if k in _UPDATABLE}
        if not fields:
            return self.get_customer(customer_id)  # nothing to change

        # build "col = %s, col = %s" safely (keys are whitelisted, values are params)
        set_clause = ", ".join(f"{col} = %s" for col in fields)
        values = list(fields.values()) + [customer_id]

        return execute(
            f"UPDATE customers SET {set_clause} WHERE id = %s RETURNING *",
            values,
        )

    # DELETE (soft delete)
    def deactivate_customer(self, customer_id):
        return execute(
            "UPDATE customers SET is_active = FALSE WHERE id = %s RETURNING *",
            (customer_id,),
        )