"""Test fixture: Class with single responsibility (no SRP violation)."""


class UserRepository:
    """Class with single responsibility: data access.

    This class is focused solely on retrieving and querying user data
    from the database. It follows the Repository pattern and has a
    single, well-defined responsibility.
    """

    def __init__(self, database) -> None:
        self.db = database

    def get(self, user_id) -> None:
        """Get user by ID."""
        return self.db.query(f"SELECT * FROM users WHERE id = {user_id}")

    def get_by_email(self, email) -> None:
        """Get user by email address."""
        return self.db.query(f"SELECT * FROM users WHERE email = '{email}'")

    def get_by_username(self, username) -> None:
        """Get user by username."""
        return self.db.query(f"SELECT * FROM users WHERE username = '{username}'")

    def find(self, criteria) -> None:
        """Find users matching criteria."""
        return self.db.search("users", criteria)

    def find_all(self) -> None:
        """Find all users."""
        return self.db.query("SELECT * FROM users")

    def find_active(self) -> None:
        """Find active users."""
        return self.db.query("SELECT * FROM users WHERE active = 1")

    def fetch_all(self) -> None:
        """Fetch all users from database."""
        return self.db.fetch_all("users")

    def query(self, sql) -> None:
        """Execute custom SQL query."""
        return self.db.query(sql)

    def query_with_params(self, sql, params) -> None:
        """Execute parameterized query."""
        return self.db.query(sql, params)

    def search(self, term) -> None:
        """Search users by term."""
        return self.db.search("users", term)

    def search_by_name(self, name) -> None:
        """Search users by name."""
        return self.db.query(f"SELECT * FROM users WHERE name LIKE '%{name}%'")

    def retrieve(self, user_id) -> None:
        """Retrieve user data."""
        return self.get(user_id)

    def retrieve_multiple(self, user_ids) -> None:
        """Retrieve multiple users."""
        ids_str = ",".join(str(id) for id in user_ids)
        return self.db.query(f"SELECT * FROM users WHERE id IN ({ids_str})")


class EmailValidator:
    """Class with single responsibility: email validation.

    This class is focused solely on validating email addresses
    using various validation rules.
    """

    def validate(self, email) -> None:
        """Validate email format."""
        return self.validate_format(email) and self.validate_domain(email)

    def validate_format(self, email) -> None:
        """Validate email format with regex."""
        import re

        pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        return re.match(pattern, email) is not None

    def validate_domain(self, email) -> None:
        """Validate email domain exists."""
        domain = email.split("@")[1] if "@" in email else None
        return domain and "." in domain

    def validate_length(self, email) -> None:
        """Validate email length."""
        return 5 <= len(email) <= 254

    def check_format(self, email) -> None:
        """Check if email format is valid."""
        return self.validate_format(email)

    def check_blacklist(self, email) -> None:
        """Check if email domain is blacklisted."""
        blacklist = ["spam.com", "temp.com"]
        domain = email.split("@")[1] if "@" in email else None
        return domain not in blacklist

    def verify(self, email) -> None:
        """Verify email is valid."""
        return self.validate(email)

    def verify_syntax(self, email) -> None:
        """Verify email syntax."""
        return "@" in email and "." in email
