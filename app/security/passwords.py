"""
Password hashing with bcrypt (salted).

WHY WE HASH:
We never store a user's real password in the database. If the database were ever
leaked, plain-text passwords would expose every account. Instead we store a
one-way "hash" -- a scrambled version that can't be reversed back into the
password.

WHY BCRYPT + SALT:
bcrypt automatically generates a random "salt" (extra random data) for each
password and mixes it into the hash. This means two users with the SAME password
still get DIFFERENT hashes, so an attacker can't tell they match, and can't use
precomputed "rainbow table" lookups to crack them. bcrypt is also deliberately
slow, which makes brute-force guessing expensive.
"""
import bcrypt # the hashing library (installed via requirements.txt)


def hash_password(plain: str) -> str:
    """
    Turn a plain-text password into a secure bcrypt hash for storing in the DB.

    Steps:
      1. plain.encode("utf-8")  -> bcrypt works on raw bytes, not str, so we
                                    convert the password text into bytes.
      2. bcrypt.gensalt()       -> generate a fresh random salt for THIS password.
      3. bcrypt.hashpw(...)     -> combine the password + salt into one hash.
                                    (The salt is stored inside the hash string
                                    itself, so we don't need a separate column.)
      4. .decode("utf-8")       -> convert the resulting bytes back into a str
                                    so it can be saved in a TEXT database column.
    """
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    """
    Check whether a login attempt matches the stored hash. Returns True/False.

    We never "un-hash" the stored value (that's impossible by design). Instead,
    bcrypt.checkpw re-hashes the attempted password using the SAME salt baked
    into the stored hash, then compares the two. If they match, the password
    is correct.

    Both inputs are encoded to bytes because bcrypt operates on bytes:
      - plain  = the password the user just typed in
      - hashed = the hash we previously saved in the database
    """
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        """ If the stored value is not a valid bcrypt hash for example a corrupted or a leftover plain text value,
          chechpw raises ValueError. We treat that as a failed login instead of letting the whole request crash.
          """
        return False
