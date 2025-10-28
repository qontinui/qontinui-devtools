"""Test fixture: Class with single responsibility (no SRP violation)."""


class UserRepository:
    """Class with single responsibility: data access.

    This class is focused solely on retrieving and querying user data
    from the database. It follows the Repository pattern and has a
    single, well-defined responsibility.
    """

    def __init__(self, database):
        self.db = database

    def get(self, user_id):
        """Get user by ID."""
        return self.db.query(f"SELECT * FROM users WHERE id = {user_id}")

    def get_by_email(self, email):
        """Get user by email address."""
        return self.db.query(f"SELECT * FROM users WHERE email = '{email}'")

    def get_by_username(self, username):
        """Get user by username."""
        return self.db.query(f"SELECT * FROM users WHERE username = '{username}'")

    def find(self, criteria):
        """Find users matching criteria."""
        return self.db.search("users", criteria)

    def find_all(self):
        """Find all users."""
        return self.db.query("SELECT * FROM users")

    def find_active(self):
        """Find active users."""
        return self.db.query("SELECT * FROM users WHERE active = 1")

    def fetch_all(self):
        """Fetch all users from database."""
        return self.db.fetch_all("users")

    def query(self, sql):
        """Execute custom SQL query."""
        return self.db.query(sql)

    def query_with_params(self, sql, params):
        """Execute parameterized query."""
        return self.db.query(sql, params)

    def search(self, term):
        """Search users by term."""
        return self.db.search("users", term)

    def search_by_name(self, name):
        """Search users by name."""
        return self.db.query(f"SELECT * FROM users WHERE name LIKE '%{name}%'")

    def retrieve(self, user_id):
        """Retrieve user data."""
        return self.get(user_id)

    def retrieve_multiple(self, user_ids):
        """Retrieve multiple users."""
        ids_str = ",".join(str(id) for id in user_ids)
        return self.db.query(f"SELECT * FROM users WHERE id IN ({ids_str})")


class EmailValidator:
    """Class with single responsibility: email validation.

    This class is focused solely on validating email addresses
    using various validation rules.
    """

    def validate(self, email):
        """Validate email format."""
        return self.validate_format(email) and self.validate_domain(email)

    def validate_format(self, email):
        """Validate email format with regex."""
        import re
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return re.match(pattern, email) is not None

    def validate_domain(self, email):
        """Validate email domain exists."""
        domain = email.split('@')[1] if '@' in email else None
        return domain and '.' in domain

    def validate_length(self, email):
        """Validate email length."""
        return 5 <= len(email) <= 254

    def check_format(self, email):
        """Check if email format is valid."""
        return self.validate_format(email)

    def check_blacklist(self, email):
        """Check if email domain is blacklisted."""
        blacklist = ['spam.com', 'temp.com']
        domain = email.split('@')[1] if '@' in email else None
        return domain not in blacklist

    def verify(self, email):
        """Verify email is valid."""
        return self.validate(email)

    def verify_syntax(self, email):
        """Verify email syntax."""
        return '@' in email and '.' in email
