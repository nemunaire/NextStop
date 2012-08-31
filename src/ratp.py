#! /usr/bin/python3

import re
import http.cookiejar, urllib.request
import bs4
from unidecode import unidecode

def getInfoPage (page):
  conn = http.client.HTTPConnection("wap.ratp.fr", timeout=15)
  #We need a "proper" UA otherwise ratp.fr gives us a boggus page
  conn.request("GET", page, "",
      {"User-Agent":"Mozilla/5.0 (X11; Linux x86_64; rv:10.0.4) "
        + "Gecko/20100101 Firefox/10.0.4 Iceweasel/10.0.4"})
  res = conn.getresponse()
  data = str(res.read())
  conn.close()
  return data

# Removes bizarre things from strings
def cleanString(mystr):
  mystr = re.sub(r'\\\'', '\'', mystr)
  mystr = re.sub(r'[-]', ' ', mystr)
  mystr = re.sub(r'[ ][ ]+', ' ', mystr)
  return unidecode(mystr)

def searchNameInData(name, data):
  return re.search(r'%s' % cleanString(name),
      cleanString(data),
      re.IGNORECASE)

# Returns a hashtable of all the stations of the line in both directions
def getAllStations(transport, line):
  page = getInfoPage("/siv/schedule?stationname=*&reseau=%s&linecode=%s"
      % (transport, line))
  soup = bs4.BeautifulSoup(page)
  stations = {}
  directions = {}
  links = soup.findAll('a')
  for link in links:
    if re.search(r'directionsens=', str(link)):
      directions[cleanString(link.string)] = link['href']
    elif re.search(r'stationid=', str(link)):
      stations[cleanString(link.string)] = link['href']
  if len(directions) > 0:
    stations = {}
    for name in directions:
      print("Direction: %s", name)
      page = getInfoPage("siv" + directions[name])
      soup = bs4.BeautifulSoup(page)
      links = soup.findAll('a')
      for link in links:
        if re.search(r'stationid=', str(link)):
          stations[cleanString(link.string)] = link['href']
  return stations

# Returns a list of all the stations of the line in both directions
def getAllStationsUrls(transport, line):
  page = getInfoPage("/siv/schedule?stationname=*&reseau=%s&linecode=%s"
      % (transport, line))
  soup = bs4.BeautifulSoup(page)
  stations = []
  directions = {}
  links = soup.findAll('a')
  for link in links:
    if re.search(r'directionsens=', str(link)):
      directions[cleanString(link.string)] = link['href']
    elif re.search(r'stationid=', str(link)):
      stations.append((cleanString(link.string), link['href']))
  if len(directions) > 0:
    stations = []
    for name in directions:
      page = getInfoPage("/siv/" + directions[name])
      soup = bs4.BeautifulSoup(page)
      links = soup.findAll('a')
      for link in links:
        if re.search(r'stationid=', str(link)):
          stations.append((cleanString(link.string), link['href']))
  return stations

# Returns the time at a specific station
def getStationTimes(soup, station):
  divs = soup.findAll('div')
  currentdest = ""
  times = []
  for div in divs:
    try:
      cl = div['class'][0]
      if re.search(r'schmsg', cl):
        if div.b is not None:
          times.append((cleanString(div.b.string),
            cleanString(currentdest), station))
      if re.search(r'bg', cl):
        m = re.search(r'([-_a-zA-Z-9]+[^>]*[-_a-zA-Z-9]+)', str(div.string))
        if m is not None:
          currentdest = m.group()
    except KeyError:
      next
  return times



def getNextStopsAtStation(transport, line, station):
  stations = getAllStationsUrls(transport, line)
  results = []
  for key, url in stations:
    if searchNameInData(station, key):
      page = getInfoPage("/siv" + url)
      soup = bs4.BeautifulSoup(page)
      results += getStationTimes(soup, key)
  return results

def extractInformation(transport,
    line,
    station):
  if station != "":
    times = getNextStopsAtStation(transport, line, station)
    for time, direction, stationname in times:
      print("Next %s %s at %s going to %s at %s" %
          (transport, line, stationname, direction, time))
  else:
    stations = getAllStations(transport, line)
    if len(stations) > 0:
      for name in stations:
        print("Station %s." % name)
      return 0
    else:
      print("No station found.")
