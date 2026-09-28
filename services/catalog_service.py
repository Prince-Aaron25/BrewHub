from services.common import Service, text_value, amount
from repositories.queries import one, all_rows, insert


class CatalogService(Service):
    def categories(self):
        with self.tx("menu") as cur:
            return all_rows(cur,"SELECT * FROM categories ORDER BY category_name")

    def save_category(self, name, category_id=None):
        name = text_value(name,"Category",100)
        with self.tx("manage",True) as cur:
            if one(cur,"SELECT category_id FROM categories WHERE category_name=%s AND category_id<>%s",(name,category_id or 0)):
                raise ValueError("Category already exists.")
            if category_id:
                cur.execute("UPDATE categories SET category_name=%s WHERE category_id=%s",(name,category_id))
                return category_id
            return insert(cur,"INSERT INTO categories(category_name) VALUES(%s)",(name,))

    def delete_category(self, category_id):
        with self.tx("manage",True) as cur:
            if one(cur,"SELECT product_id FROM products WHERE category_id=%s LIMIT 1",(category_id,)):
                raise ValueError("Move this category's products to another category first.")
            cur.execute("DELETE FROM categories WHERE category_id=%s",(category_id,))

    def products(self, search="", category_id=None, include_unavailable=False):
        permission = "manage" if include_unavailable else "menu"
        with self.tx(permission) as cur:
            sql = """SELECT p.*,c.category_name FROM products p LEFT JOIN categories c
                     ON p.category_id=c.category_id WHERE p.product_name LIKE %s"""
            args = ["%"+search+"%"]
            if not include_unavailable:
                sql += " AND p.availability=1"
            if category_id:
                sql += " AND p.category_id=%s"
                args.append(category_id)
            return all_rows(cur,sql+" ORDER BY p.product_name",tuple(args))

    def save_product(self, name, category_id, description, price, image_path, available, product_id=None):
        name, description = text_value(name,"Product name",100), text_value(description,"Description",255,False)
        price = amount(price,"Price",True)
        image_path = text_value(image_path,"Image path",255,False)
        with self.tx("manage",True) as cur:
            if not one(cur,"SELECT category_id FROM categories WHERE category_id=%s",(category_id,)):
                raise ValueError("Choose a category first.")
            values = (name,category_id,description,price,image_path,bool(available))
            if product_id:
                cur.execute("""UPDATE products SET product_name=%s,category_id=%s,description=%s,
                    price=%s,image_path=%s,availability=%s WHERE product_id=%s""", values+(product_id,))
                return product_id
            return insert(cur,"""INSERT INTO products(product_name,category_id,description,price,image_path,availability)
                                 VALUES(%s,%s,%s,%s,%s,%s)""",values)

    def delete_product(self, product_id):
        with self.tx("manage",True) as cur:
            if one(cur,"SELECT order_item_id FROM order_items WHERE product_id=%s LIMIT 1",(product_id,)):
                cur.execute("UPDATE products SET availability=0 WHERE product_id=%s",(product_id,))
                return "Product has order history, so it was marked unavailable."
            cur.execute("DELETE FROM product_ingredients WHERE product_id=%s",(product_id,))
            cur.execute("DELETE FROM products WHERE product_id=%s",(product_id,))
            return "Unused product deleted."

    def recipe(self, product_id):
        with self.tx("manage") as cur:
            return all_rows(cur,"""SELECT pi.*,i.ingredient_name,i.unit FROM product_ingredients pi
                JOIN ingredients i ON pi.ingredient_id=i.ingredient_id WHERE pi.product_id=%s
                ORDER BY i.ingredient_name""",(product_id,))

    def save_recipe_line(self, product_id, ingredient_id, quantity):
        quantity = amount(quantity,"Recipe quantity",True)
        with self.tx("manage",True) as cur:
            for table, field, value in (("products","product_id",product_id),("ingredients","ingredient_id",ingredient_id)):
                if not one(cur,f"SELECT {field} FROM {table} WHERE {field}=%s",(value,)):
                    raise ValueError("Choose an existing product and ingredient.")
            cur.execute("""INSERT INTO product_ingredients(product_id,ingredient_id,quantity_required)
                VALUES(%s,%s,%s) ON DUPLICATE KEY UPDATE quantity_required=%s""",(product_id,ingredient_id,quantity,quantity))

    def remove_recipe_line(self, product_id, ingredient_id):
        with self.tx("manage",True) as cur:
            cur.execute("DELETE FROM product_ingredients WHERE product_id=%s AND ingredient_id=%s",(product_id,ingredient_id))

