from datetime import datetime, timedelta
import json
import requests
import sys

from lxml import html
from icalendar import Calendar, Event, vText
import pytz

tz = pytz.timezone("Europe/Paris")


def parse(filename):
    with open(filename) as f:
        data = f.read()
    tree = html.fromstring(data)

    rows = tree.xpath('//table[@class="liste"]/tbody/tr')
    for row in rows:
        cols = row.findall("td")
        try:
            match_index = int(cols[0].text)
        except (ValueError, TypeError):
            continue
        print(match_index)
        date = cols[1].text
        time = cols[2].text
        home = cols[3].find("a").text.title()
        away = cols[4].find("a").text.title()
        # import pdb; pdb.set_trace()
        location_id = cols[6].find("a").get("href").split("'")[1]
        resp = requests.get("http://resultats.ffbb.com/here/here_popup.php?id={}".format(location_id))
        subtree = html.fromstring(resp.content)
        scripts = subtree.find("head").findall("script")
        location = None
        for script in scripts:
            if not script.text or not "CDATA" in script.text:
                continue
            start_data = script.text.find("{")
            end_data = script.text.find("}")
            data = json.loads(script.text[start_data : end_data + 1])
            location = "{} {} {}".format(data["title"].title(), data["adress"], data["city"])
        dt = datetime.strptime("{} {}".format(date, time), "%d/%m/%Y %H:%M")
        dt_with_tz = dt.astimezone(tz)
        yield match_index, dt_with_tz, home, away, location


def main():
    cal = Calendar()
    cal.add("prodid", "-//My calendar product//mxm.dk//")
    cal.add("version", "2.0")
    for ind, dt, home, away, location in parse(sys.argv[1]):
        event = Event()
        event.add("summary", "Match {} - {} contre {}".format(ind, home, away))
        event.add("dtstart", dt)
        event.add("dtend", dt + timedelta(hours=2))
        event["location"] = vText(location)
        cal.add_component(event)
    with open("example.ics", "wb") as f:
        f.write(cal.to_ical())


if __name__ == "__main__":
    main()
