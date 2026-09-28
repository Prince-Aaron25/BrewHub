from decimal import Decimal
from services.common import Service, text_value, amount
from repositories.queries import one, all_rows, insert
from models.inventory import Ingredient


def record_stock(cur, ingredient_id, kind, quantity, reason, user_id, order_id=None):
    cur.execute("""INSERT INTO inventory_transactions(ingredient_id,transaction_type,quantity,remarks,performed_by,order_id)
        VALUES(%s,%s,%s,%s,%s,%s)""",(ingredient_id,kind,quantity,reason,user_id,order_id))


class InventoryService(Service):
    def ingredients(self, low_only=False):
        with self.tx("manage") as cur:
            rows = all_rows(cur,"SELECT * FROM ingredients ORDER BY ingredient_name")
            for r in rows:
                r["quantity"] = r["quantity"] or Decimal("0.00")
                r["reorder_level"] = r["reorder_level"] or Decimal("0.00")
                r["low_stock"] = Ingredient(**r).is_low()
            return [r for r in rows if r["low_stock"]] if low_only else rows

    def save_ingredient(self, name, unit, reorder, ingredient_id=None):
        name, unit = text_value(name,"Ingredient",100), text_value(unit,"Unit",30)
        reorder = amount(reorder,"Reorder level")
        with self.tx("manage",True) as cur:
            if ingredient_id:
                row = one(cur,"SELECT * FROM ingredients WHERE ingredient_id=%s",(ingredient_id,))
                if not row:
                    raise ValueError("Ingredient not found.")
                if row["unit"] != unit:
                    raise ValueError("Unit cannot change after creation. Create another ingredient with the correct unit.")
                cur.execute("UPDATE ingredients SET ingredient_name=%s,reorder_level=%s WHERE ingredient_id=%s",(name,reorder,ingredient_id))
                return ingredient_id
            return insert(cur,"INSERT INTO ingredients(ingredient_name,unit,quantity,reorder_level) VALUES(%s,%s,0,%s)",(name,unit,reorder))

    def adjust(self, ingredient_id, kind, quantity, reason):
        quantity = amount(quantity,"Stock quantity")
        reason = text_value(reason,"Reason",255)
        if kind not in ("Stock In","Stock Out","Adjustment"):
            raise ValueError("Invalid stock action.")
        if kind != "Adjustment" and quantity == 0:
            raise ValueError("Quantity must be greater than zero.")
        with self.tx("manage",True) as cur:
            row = one(cur,"SELECT quantity FROM ingredients WHERE ingredient_id=%s FOR UPDATE",(ingredient_id,))
            if not row:
                raise ValueError("Ingredient not found.")
            current = row["quantity"] or Decimal("0.00")
            new = quantity if kind == "Adjustment" else current + (quantity if kind == "Stock In" else -quantity)
            if new < 0:
                raise ValueError("Stock cannot become negative.")
            amount(new,"Resulting stock")
            delta = new-current
            cur.execute("UPDATE ingredients SET quantity=%s WHERE ingredient_id=%s",(new,ingredient_id))
            # Adjustment quantities store signed differences; Stock In/Out store magnitudes.
            record_stock(cur,ingredient_id,kind,delta if kind == "Adjustment" else quantity,reason,self.user.user_id)

    def history(self):
        with self.tx("manage") as cur:
            return all_rows(cur,"""SELECT t.*,i.ingredient_name,i.unit,u.full_name AS performed_by_name
                FROM inventory_transactions t JOIN ingredients i ON i.ingredient_id=t.ingredient_id
                LEFT JOIN users u ON u.user_id=t.performed_by ORDER BY t.transaction_id DESC""")

    def delete_ingredient(self, ingredient_id):
        with self.tx("manage",True) as cur:
            for table in ("product_ingredients","inventory_transactions","order_stock"):
                if one(cur,f"SELECT ingredient_id FROM {table} WHERE ingredient_id=%s LIMIT 1",(ingredient_id,)):
                    raise ValueError("Ingredient is used by recipes or stock history and must be retained.")
            cur.execute("DELETE FROM ingredients WHERE ingredient_id=%s",(ingredient_id,))

