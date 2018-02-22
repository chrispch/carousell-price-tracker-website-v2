# import sys, os
# abspath = os.path.dirname(__file__)
# sys.path.append(abspath)
# os.chdir(abspath)
from database import create_data
from scrapper import scrap, filter_data, exception_words, price_range, load_links


urls_file = "urls.csv"
urls = load_links(urls_file)


# saves crawled data in database
def scrap_into_database(urls):
    print("Scrapping into database")
    for category, url in urls.items():
        print(category, url)
        data = scrap(url)
        data = filter_data(data, exception_words, exception_words, price_range)
        for d in data:
            create_data(d["name"], d["price"], d["date"], d["link"], category)


scrap_into_database(urls)