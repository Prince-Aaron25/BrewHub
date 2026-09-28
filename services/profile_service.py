from services.common import Service, text_value, email_value
from services.auth_service import HASHER, password_value, verify
from repositories.queries import one, all_rows


class ProfileService(Service):
    def get_profile(self):
        with self.tx("profile") as cur:
            return one(cur, "SELECT user_id,full_name,email,phone,role,status FROM users WHERE user_id=%s", (self.user.user_id,))

    def update(self, name, email, phone):
        name, email = text_value(name, "Name", 100), email_value(email)
        phone = text_value(phone, "Phone", 20, False)
        with self.tx("profile", True) as cur:
            if one(cur, "SELECT user_id FROM users WHERE email=%s AND user_id<>%s", (email, self.user.user_id)):
                raise ValueError("That email belongs to another account.")
            cur.execute("UPDATE users SET full_name=%s,email=%s,phone=%s WHERE user_id=%s", (name,email,phone,self.user.user_id))

    def change_password(self, current, new):
        password_value(new)
        with self.tx("profile", True) as cur:
            row = one(cur, "SELECT password FROM users WHERE user_id=%s", (self.user.user_id,))
            if not verify(row["password"], current):
                raise ValueError("Current password is incorrect.")
            cur.execute("UPDATE users SET password=%s WHERE user_id=%s", (HASHER.hash(new), self.user.user_id))

    def users(self):
        with self.tx("manage") as cur:
            return all_rows(cur, "SELECT user_id,full_name,email,phone,role,status FROM users ORDER BY user_id")

    def set_status(self, user_id, status):
        if status not in ("active", "inactive"):
            raise ValueError("Invalid account status.")
        with self.tx("manage", True) as cur:
            target = one(cur, "SELECT * FROM users WHERE user_id=%s", (user_id,))
            if not target:
                raise ValueError("User not found.")
            if target["role"] == "admin":
                raise ValueError("Admin accounts are managed using the local setup tool.")
            cur.execute("UPDATE users SET status=%s WHERE user_id=%s", (status,user_id))

    def reset_customer_password(self, user_id, new):
        password_value(new)
        with self.tx("manage", True) as cur:
            target = one(cur, "SELECT role FROM users WHERE user_id=%s", (user_id,))
            if not target or target["role"] != "customer":
                raise ValueError("Select a customer account.")
            cur.execute("UPDATE users SET password=%s WHERE user_id=%s", (HASHER.hash(new),user_id))

