import csv
import os

from benchmark import WhooshLikeSpec
from whoosh import fields


class Customers(WhooshLikeSpec):
    name = "customers"
    main_field = "city"
    headline_field = "first_name"
    default_query = "London"

    def whoosh_schema(self):
        schema = fields.Schema(
            customer_id=fields.ID(stored=True, unique=True),
            first_name=fields.TEXT(stored=True),
            last_name=fields.TEXT(stored=True),
            company=fields.TEXT(stored=True),
            city=fields.TEXT(stored=True),
            country=fields.TEXT(stored=True),
            email=fields.TEXT(stored=True),
            subscription_date=fields.TEXT(stored=True),
            website=fields.TEXT(stored=True),
        )
        return schema

    def documents(self):
        basedir = os.path.join(self.options.dir, "customers-2000000")
        path = os.path.join(basedir, "customers-2000000.csv")
        count = 0
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield {
                    "customer_id": row["Customer Id"],
                    "first_name": row["First Name"],
                    "last_name": row["Last Name"],
                    "company": row["Company"],
                    "city": row["City"],
                    "country": row["Country"],
                    "email": row["Email"],
                    "subscription_date": row["Subscription Date"],
                    "website": row["Website"],
                }
                count += 1
                if self.options.upto and count >= int(self.options.upto):
                    break
