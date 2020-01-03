import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine('postgresql://nvuzmytodgzcae:c4907caa27275feb3ec78f5ced580ba370cd94f26f5f16a28f40051f7f81ac8d@ec2-54-163-234-44.compute-1.amazonaws.com:5432/df6ljihfevamaa')
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv")
    reader = csv.reader(f)
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                    {"isbn": isbn, "title": title, "author": author, "year": year})
        print(f"Added books with title {title} and Author {author} .")
    db.commit()

if __name__ == "__main__":
    main()
