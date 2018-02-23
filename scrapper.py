import requests
from bs4 import BeautifulSoup
import difflib
from datetime import date, timedelta
import csv


exception_words = ["spoilt", "broken", "1/10", "2/10", "3/10", "4/10"]
price_range = (1, 9999)  # (min, max)
categories = ["Property", "Electronics", "Jobs", "Mobiles & Tablets", "Women's Fashion",
              "Men's Fashion", "Luxury", "Health & Beauty", "Video Gaming", "Toys & Games",
              "Photography", "Sports", "Music & Media", "Antiques"]  # categories to scrap
csv_file = "urls.csv"


# returns links to all categories and subcategories on Carousell
def get_links():
    urls = {}
    r = requests.get("https://carousell.com/")
    c = r.content
    soup = BeautifulSoup(c, "html.parser")
    nav_bar = soup.find("div", {"id": "navbarCategoryMenuButtonMenu-0"})
    links = nav_bar.find_all("a")
    if "All" in categories:
        # get all links
        for l in links:
            h = l.get('href')  # href link
            t = l.get_text()  # category name
            urls[t] = "https://carousell.com" + h + "?sort_by=time_created%2Cdescending"
    else:
        # get links specified in categories
        for l in links:
            h = l.get('href')  # href link
            t = l.get_text()  # category name
            if t in categories:
           	 urls[t] = "https://carousell.com" + h + "?sort_by=time_created%2Cdescending"
    print(urls)
    return urls


# save links into external file
def save_links(urls, file):
    with open(file, 'w', newline='') as csvfile:
        urlwriter = csv.writer(csvfile, delimiter=' ')
        for k,v in urls.items():
            urlwriter.writerow([k, v])


# gets urls from external file
def load_links(file):
    with open(file, newline="") as csvfile:
        urlsreader = csv.reader(csvfile, delimiter=" ")
        urls = {}
        for row in urlsreader:
            urls[row[0]] = row[1]
    return urls


# query and collect listings for a given URL and returns an array with data
def scrap(url):
    try:
        data = []  # array to be returned
        # request data
        r = requests.get(url)
        c = r.content
        soup = BeautifulSoup(c, "html.parser")
        names = soup.find_all("h4", {"id": "productCardTitle"})  # name of listing
        info = soup.find_all("dl")  # contains price and desc
        time_ago = soup.find_all("time")  # time of posting
        hyperlinks = soup.find_all("a", {"id": "productCardThumbnail"})  # link to listing

        # remove duplicate hyperlinks
        for i in range(len(hyperlinks) - 1, -1, -1):
            if i % 2 == 0:
                hyperlinks.pop(i)
        current_date = date.today()

        # process list of listings from page
        for n, i, t, h in zip(names, info, time_ago, hyperlinks):
            # parse name
            name = n.text
            x = i.find_all("dd")
            # parse price
            price_text = x[0].text
            price = float("".join(ele for ele in price_text if ele.isdigit()))
            # parse description
            desc = x[1].text
            # parse hyperlink
            href = "https://carousell.com" + h.get("href")
            # parse time ago data
            t_split = t.text.split(" ")
            if t_split[0] == "last":
                t_split[0] = "1"
            if "yesterday" in t_split[0]:
                d = current_date - timedelta(days=1)
            elif "year" in t_split[1]:
                d = date(current_date.year -
                         int(t_split[0]), current_date.month, current_date.day)
            elif "month" in t_split[1]:
                if current_date.month <= int(t_split[0]):
                    d = date(current_date.year - 1, 12 -
                             int(t_split[0]) + current_date.month, current_date.day)
                else:
                    d = date(current_date.year, current_date.month -
                             int(t_split[0]), current_date.day)
            elif "day" in t_split[1]:
                d = current_date - timedelta(days=int(t_split[0]))
            else:
                d = current_date

            data.append({"name": name, "price": price, "date": str(d), "link": href,
                         "desc": desc})

        return data

    except requests.exceptions.RequestException:
        print("Connection failed")


# filter listings data to weed out troll listings
def filter_data(data, name_blacklist, desc_blacklist, price_range):
    filtered_data = []
    for d in data:
        valid = True  # set data to successfully pass filter at first
        if name_blacklist:
            for n in name_blacklist:
                if n in d["name"]:
                    valid = False
        if desc_blacklist:
            for n in desc_blacklist:
                if n in d["desc"]:
                    valid = False
        if price_range:
            if not price_range[0] < d["price"] < price_range[1]:
                valid = False
        if valid:
            d.pop("desc")  # remove description information to reduce data size
            filtered_data.append(d)
    return filtered_data


def search_data(data, search_terms, tolerance=1):
    search_results = []
    temp_results = []
    if type(search_terms) is str:
        search_terms = search_terms.split(" ")
    for f in search_terms:
        # runs for the first filter
        if not search_results:
            for listing in data:
                if type(listing) is dict:
                    # checks to see if label matches any word in name, to given tolerance, and returns results
                    for word in listing["name"].split(" "):
                        s = difflib.SequenceMatcher(None, f.lower(), word.lower())
                        if s.quick_ratio() >= tolerance or f.lower() in word.lower():
                            print(f.lower())
                            print(word.lower())
                            if listing not in search_results:
                                search_results.append(listing)
                else:
                    # checks to see if label matches any word in name, to given tolerance, and returns results
                    for word in listing.name.split(" "):
                        s = difflib.SequenceMatcher(None, f.lower(), word.lower())
                        if s.quick_ratio() >= tolerance or f.lower() in word.lower():
                            if listing not in search_results:
                                search_results.append(listing)

        # subsequent filtered results stored in temp_results for comparison
        else:
            for listing in data:
                # checks to see if label matches any word in name, to given tolerance, and returns results
                if type(listing) is dict:
                    for word in listing["name"].split(" "):
                        s = difflib.SequenceMatcher(None, f.lower(), word.lower())
                        if s.quick_ratio() >= tolerance or f.lower() in word.lower():
                            if listing not in temp_results:
                                temp_results.append(listing)
                else:
                    for word in listing.name.split(" "):
                        s = difflib.SequenceMatcher(None, f.lower(), word.lower())
                        if s.quick_ratio() >= tolerance or f.lower() in word.lower():
                            if listing not in temp_results:
                                temp_results.append(listing)
            # intersects all new search results and saves it in search_results
            search_results = list(
                filter(lambda x: x in search_results, temp_results))
            temp_results = []

    return search_results


urls = get_links()
save_links(urls, csv_file)


# loaded = load_links(csv_file)
# ls = list(loaded.keys())
# ls.sort()
# for i in ls:
#     print(i)
# get_links()
# print(scrap("https://carousell.com/categories/electronics-7/audio-207/"))
# print(filter_data(scrap("https://carousell.com/categories/electronics-7/audio-207/"), exception_words, exception_words, price_range))
# generate_labels(data["sennheiser"])
# print(search_database(["sennheiser", "headphones"], [data["sennheiser"]]))

