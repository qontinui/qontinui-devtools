"""Test fixture: Class with multiple responsibilities (SRP violation)."""


class UserManager:
    """Class with multiple responsibilities - violates SRP.

    This class handles:
    1. Data access (fetching user data)
    2. Validation (email, password checks)
    3. Business logic (scoring, registration)
    4. Persistence (database, cache)
    5. Presentation (formatting, rendering)
    """

    def __init__(self, db_connection):
        self.db = db_connection
        self.cache = {}

    # Data Access responsibility
    def get_user(self, user_id):
        """Fetch user by ID."""
        return self.db.query(f"SELECT * FROM users WHERE id = {user_id}")

    def find_users(self, query):
        """Find users matching query."""
        return self.db.search("users", query)

    def fetch_user_data(self, user_id):
        """Fetch complete user data."""
        return self.db.fetch(user_id)

    def query_users_by_email(self, email):
        """Query users by email address."""
        return self.db.query(f"SELECT * FROM users WHERE email = '{email}'")

    def retrieve_user_profile(self, user_id):
        """Retrieve user profile information."""
        return self.db.get_profile(user_id)

    # Validation responsibility
    def validate_email(self, email):
        """Validate email format."""
        import re

        pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        return re.match(pattern, email) is not None

    def check_password_strength(self, password):
        """Check if password meets strength requirements."""
        return len(password) >= 8 and any(c.isupper() for c in password)

    def verify_user_credentials(self, username, password):
        """Verify username and password."""
        user = self.get_user_by_username(username)
        return user and user.password == password

    def assert_user_exists(self, user_id):
        """Assert that user exists."""
        user = self.get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        return True

    # Business Logic responsibility
    def calculate_user_score(self, user_id):
        """Calculate user engagement score."""
        user = self.get_user(user_id)
        return user.posts * 10 + user.comments * 5

    def process_registration(self, user_data):
        """Process user registration."""
        if not self.validate_email(user_data["email"]):
            raise ValueError("Invalid email")
        return self.save_to_database(user_data)

    def compute_user_rank(self, user_id):
        """Compute user ranking."""
        score = self.calculate_user_score(user_id)
        all_scores = [self.calculate_user_score(u.id) for u in self.find_users({})]
        return sorted(all_scores).index(score) + 1

    def execute_user_migration(self, user_id, target_system):
        """Execute user data migration."""
        user = self.get_user(user_id)
        return target_system.import_user(user)

    # Persistence responsibility
    def save_to_database(self, user_data):
        """Save user to database."""
        return self.db.insert("users", user_data)

    def load_from_cache(self, user_id):
        """Load user from cache."""
        return self.cache.get(user_id)

    def store_in_cache(self, user_id, user_data):
        """Store user in cache."""
        self.cache[user_id] = user_data

    def persist_user_changes(self, user_id, changes):
        """Persist user changes to database."""
        return self.db.update("users", user_id, changes)

    def delete_user_data(self, user_id):
        """Delete user data from database."""
        return self.db.delete("users", user_id)

    # Presentation responsibility
    def format_user_display(self, user_id):
        """Format user for display."""
        user = self.get_user(user_id)
        return f"{user.name} ({user.email})"

    def render_profile(self, user_id):
        """Render user profile HTML."""
        user = self.get_user(user_id)
        return f"<div class='profile'>{user.name}</div>"

    def display_user_summary(self, user_id):
        """Display user summary."""
        user = self.get_user(user_id)
        score = self.calculate_user_score(user_id)
        return f"{user.name}: Score {score}"

    def show_user_stats(self, user_id):
        """Show user statistics."""
        user = self.get_user(user_id)
        return {"posts": user.posts, "comments": user.comments}

    # Helper methods (mixed responsibilities)
    def get_user_by_username(self, username):
        """Get user by username."""
        return self.db.query(f"SELECT * FROM users WHERE username = '{username}'")
