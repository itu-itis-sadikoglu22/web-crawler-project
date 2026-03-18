from app.storage import Storage


def main():
    storage = Storage()
    print("Database initialized successfully.")
    print(storage.get_status())


if __name__ == "__main__":
    main()