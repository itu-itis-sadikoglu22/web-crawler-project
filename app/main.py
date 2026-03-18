# from app.storage import Storage
#
#
#def main():
   # storage = Storage()
  #  print("Database initialized successfully.")
 #   print(storage.get_status())
#
#
#if __name__ == "__main__":
 #   main() 

from app.parser import parse_html, term_frequencies


def main():
    html = """
    <html>
        <head><title>Example Page</title></head>
        <body>
            <h1>Welcome to Example</h1>
            <p>This is a crawler test page.</p>
            <a href="/about">About</a>
            <a href="https://example.com/contact">Contact</a>
        </body>
    </html>
    """

    result = parse_html("https://example.com", html)
    print(result)
    print(term_frequencies(result["body_text"]))


if __name__ == "__main__":
    main()