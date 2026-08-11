import copy
from datetime import datetime

from app.data.sample_data import CUSTOMERS


class CustomerService:

    def __init__(self):
        # makes a copy of the sample data to avoid altering the original data
        self.customers = copy.deepcopy(CUSTOMERS) 
        # finds next available id
        self.next_id = max(self.customers.keys()) + 1

    # CREATE
    def create_customer(self, name, email, phone, address, branch_id=1):
        # builds a new customer dictionary and adds it
        customer = {
            "id": self.next_id,
            "name": name,
            "email": email,
            "phone": phone,
            "address": address,
            "branch_id": branch_id,
            "created_at": datetime.now(),
            "is_active": True,
        }
        # saves the new customer in the dictionary and moves to the next_id
        self.customers[self.next_id] = customer
        self.next_id += 1
        return customer

    # READ
    def get_all_customers(self):
        # returns a list of all customers
        return list(self.customers.values())

    def get_customer(self, customer_id):
        # returns a customer with the given id, or None if not found
        return self.customers.get(customer_id)

    # UPDATE
    def update_customer(self, customer_id, updates):
        customer = self.customers.get(customer_id)
        if customer is None:
            # no customer is found with the given id
            return None
        for field, value in updates.items():
            customer[field] = value
        return customer

    # DELETE
    def deactivate_customer(self, customer_id):
        customer = self.customers.get(customer_id)
        if customer is None:
            # no customer is found with the given id
            return None
        customer["is_active"] = False
        return customer