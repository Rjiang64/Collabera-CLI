# Banking Application

## Overview

A simple command-line banking application that demonstrates Object-Oriented Programming principles. Users can log in and manage two separate bank accounts: checking and savings, each with different rules and features.

---

## How to Run

1. Enter a username (ray, ricky, or santosh)
2. Enter your PIN (0000, 1234, or 4321)
3. Choose which account to access (checking or savings)
4. Perform transactions (deposit, withdraw, check balance)

---

## Features

- **User Authentication** - Login with username and PIN
- **Two Account Types** - Checking and Savings with different rules
- **Checking Account** - Allows overdrafts up to $200
- **Savings Account** - Enforces minimum balance of $100
- **Safe Transactions** - Validates all deposits and withdrawals
- **Protected Data** - Passwords and balances are private (can't be accessed directly)

---

## Classes

### BankAccount (Parent Class)

The base class for all bank accounts. Handles basic account operations.

**Attributes:**

- `owner` - Account holder's name
- `__password` - Private PIN (hidden from outside access)
- `__balance` - Private balance (protected from direct changes)
  **Methods:**
- `deposit(amount)` - Add money to account
- `withdraw(amount)` - Remove money (checks if funds available)
- `check_balance()` - Display balance as formatted string
- `get_balance()` - Get raw balance number (for calculations)
- `set_balance(balance)` - Update balance (used by child classes)

---

### SavingsAccount (Child Class)

Inherits from BankAccount. Adds a minimum balance requirement.

**Additional Attributes:**

- `minimum_balance` - Minimum amount required ($100 default)
- `account_type` - "Savings" (for display)
  **Overridden Methods:**
- `withdraw(amount)` - Checks TWO things:
  1. Is there enough money?
  2. Will balance still be above minimum?
  - Only allows withdrawal if BOTH are true
    **Example:**

```
Balance: $200, Minimum: $100
User tries to withdraw $150
Result: $200 - $150 = $50
$50 < $100 minimum → DENIED
```

---

### CheckingAccount (Child Class)

Inherits from BankAccount. Allows going negative up to an overdraft limit.

**Additional Attributes:**

- `overdraft_limit` - How far negative allowed ($200 default)
- `account_type` - "Checking" (for display)
  **Overridden Methods:**
- `withdraw(amount)` - Allows balance to go negative
  - But only up to the overdraft limit
  - Prevents going below -$200
    **Example:**

```
Balance: $100, Overdraft Limit: $200
User tries to withdraw $250
Result: $100 - $250 = -$150
-$150 > -$200 limit → ALLOWED
User now has -$150 (owes $150)
```

---

### User

Represents a person with TWO bank accounts.

**Attributes:**

- `name` - User's name
- `password` - User's PIN (for login)
- `checking` - CheckingAccount object
- `savings` - SavingsAccount object
  **Methods:**
- `verify_password(password)` - Checks if entered PIN matches stored PIN
  - Returns True or False
    **Example:**

```python
user = User("ricky", "1234", checking_balance=500, savings_balance=500)
# User now has:
# - A checking account with $500
# - A savings account with $500
# - Both protected with PIN "1234"
```

---

## Data Storage

Users are stored in a **dictionary** (not a list) for fast lookup:

```python
users = {
    "ray": User(...),
    "ricky": User(...),
    "santosh": User(...)
}
```

**Why dictionary?** Looking up by username is instant: `users.get("ricky")`. With a list, we'd have to check each user one by one (slow).

---

## OOP Concepts Demonstrated

### 1. Encapsulation

Sensitive data is protected:

```python
self.__password = password  # Private - can't access directly
self.__balance = balance    # Private - can't change directly
```

Users can only interact through public methods:

```python
account.deposit(100)      # Safe method
account.withdraw(50)      # Safe method
# Can't do: account.__balance = 999999
```

### 2. Inheritance

Child classes reuse parent code:

```python
class SavingsAccount(BankAccount):  # Inherits from BankAccount
    def __init__(self, owner, password, balance=0, minimum_balance=100):
        super().__init__(owner, password, balance)  # Call parent's init
```

Benefits: No code duplication, easier to maintain.

### 3. Polymorphism

Same method name, different behavior:

```python
# Both have withdraw(), but different logic
checking.withdraw(100)  # Allows overdrafts
savings.withdraw(100)   # Enforces minimum balance
```

### 4. Abstraction

Users don't need to know HOW accounts work:

```python
# They just call methods
account.deposit(100)
account.withdraw(50)
# No need to know about private __balance or implementation details
```

---

## Sample Users

Three demo users are pre-loaded:

| Username | PIN  | Checking | Savings |
| -------- | ---- | -------- | ------- |
| ray      | 0000 | $500     | $500    |
| ricky    | 1234 | $500     | $500    |
| santosh  | 4321 | $500     | $500    |

---

## Program Flow

```
1. Login
   ├─ Enter username
   ├─ Check if user exists
   ├─ Enter PIN
   └─ Verify password

2. Main Menu
   ├─ Option 1: Access Checking Account
   │  ├─ Deposit
   │  ├─ Withdraw
   │  └─ Check Balance
   ├─ Option 2: Access Savings Account
   │  ├─ Deposit
   │  ├─ Withdraw
   │  └─ Check Balance
   └─ Option 3: Quit
```

## Learning Objectives

This project teaches:

- How to design classes (constructors, methods, attributes)
- How to use inheritance (parent-child relationships)
- How to protect data (private attributes)
- How to override methods (polymorphism)
- How to structure a real-world application
- Best practices in Object-Oriented Programming

---

## Author

Ricky Jiang, Santosh Nukala, Rayhaan Mohamed, Shehzeen Syed
