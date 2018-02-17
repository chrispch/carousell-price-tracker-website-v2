from bokeh.plotting import figure, output_file, show
from datetime import datetime as dt
import math
import statistics


def price_statistics(data):
    price_stats = {}
    total_price = 0
    price_list = []
    if type(data[0]) is dict:
        for d in data:
            # for calculation of average
            total_price += d["price"]
            # for finding min/max values and calculation of median
            price_list.append(d["price"])
    else:
        for d in data:
            # for calculation of average
            total_price += d.price
            # for finding min/max values and calculation of median
            price_list.append(d.price)

    price_stats["med_price"] = statistics.median(price_list)
    price_stats["ave_price"] = total_price / len(data)
    price_stats["max_price"] = max(price_list)
    price_stats["min_price"] = min(price_list)
    return price_stats


def graph(data):
    # print("graphing")
    # generate price and date lists
    # print("hi")
    prices = []
    dates = []
    i = -1
    if data:
        for d in data:
            date_split = d.date.split("-")
            date = dt(int(date_split[0]), int(date_split[1]), int(date_split[2]))
            price = d.price
            # first data
            if i == -1:
                prices.append([price, 1])
                dates.append(date)
                i += 1
            else:
                u = i
                x = u
                sort_done = False
                while not sort_done:
                    # print("Current date:", date)
                    if date < dates[u]:
                        if u == 0:
                            prices.insert(0, [price, 1])
                            dates.insert(0, date)
                            i += 1
                            sort_done = True
                            # print("inserting at pos 0")
                        elif dates[u-1] < date:
                            prices.insert(u, [price, 1])
                            dates.insert(u, date)
                            i += 1
                            sort_done = True
                            # print("inserting at pos: " + str(u))
                        else:
                            x = math.ceil(x/2)
                            u = u - x
                            u = max([u, 0])
                            # print("we're going down: " + str(u))
                    elif date == dates[u]:
                        prices[u][0] = prices[u][0] + price  # increase total price of all items on date u
                        prices[u][1] += 1  # increase number of items with date u for calculating average
                        sort_done = True
                        # print("dates are the same!")
                    elif date > dates[u]:
                        if u == i:
                            dates.append(date)
                            prices.append([price, 1])
                            i += 1
                            sort_done = True
                            # print("inserting at the end")
                        elif dates[u+1] > date:
                            prices.insert(u+1, [price, 1])
                            dates.insert(u+1, date)
                            i += 1
                            sort_done = True
                            # print("inserting at pos: " + str(u))
                        else:
                            x = math.ceil(x/2)
                            u = u + x
                            u = min([u, i])
                            # print("we're going up!: " + str(u))
                            # print("max", i)

        # find average price
        for i in range(len(prices)):
            prices[i] = prices[i][0] / prices[i][1]

        p = figure(tools="box_zoom, reset, save", logo=None, x_axis_type="datetime", responsive=True, plot_height=300, title="Price - Time")

        p.line(dates, prices)
    else:
        p = figure(tools="", logo=None, x_axis_type="datetime", responsive=True, plot_height=300, title="Price - Time")
        p.line(dates, prices)

    output_file("./templates/graph.html")
    show(p)
