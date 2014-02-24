import json
import os
from urlparse import urlparse
from urlparse import urljoin
import urllib
import urllib2
from urllib2 import Request, urlopen, URLError, HTTPError
import hashlib
import logging
import robotparser
from collections import deque
from sgmllib import SGMLParser
import heapq
from bs4 import BeautifulSoup
import re


logging.basicConfig(format='%(asctime)s %(message)s',filename='console.log',level=logging.DEBUG)


class URLLister(SGMLParser):
        def reset(self):
                SGMLParser.reset(self)
                self.urls = []

        def start_a(self, attrs):
                href = [v for k, v in attrs if k=='href']
                if href:
                        self.urls.extend(href)

class URL():
        
        def __init__(self,url):
                self.rawUrl = url
                self.parsedUrl= urlparse(url)
                self.fileName = hashlib.md5(self.parsedUrl.geturl().split('#')[0]).hexdigest()
                self.isCrawlable = self.checkCrawlable()
                #self.score= None
                #self.count=None

        def checkCrawlable(self):
                try:
                        rp = robotparser.RobotFileParser()
                        roboURL = self.parsedUrl.scheme + "://" + self.parsedUrl.netloc + "/robots.txt"
                        
                        if (self.parsedUrl.scheme == "http") or (self.parsedUrl.scheme== "https"):
                                rp.set_url(roboURL)
                                rp.read()
                                return rp.can_fetch("*", self.parsedUrl.geturl())
                        return False
                
                except KeyError:
                        return True
                except IOError:
                        return False
                

eCount=0
class Crawler():
        
        def __init__(self):
                self.count=0
                #self.eCount=0
                #self.errorCount=0
                self.serachQuery= None
                self.dictionary = {}
                self.qDictionary = {}
                self.urlList = []

        #Takes Search Query and returns top 10 results from google custom search
        def getURLFromGoogle(self,searchQuery):

                #Create a Query String
                query = urllib.urlencode({'q': searchQuery})

                #url Which returns a Jason Object of Serach results
                url ='https://www.googleapis.com/customsearch/v1?key=AIzaSyBIv_rONfyzaPkC0R56iwgjBuW_ikyzHyM&cx=001037612827627523088:leq0iecmusa&%s&filter=1&start=1&num=10' % query
                req = urllib2.Request(url,None,{ 'User-Agent' : 'sscrawler' , 'From':'skn262@nyu.edu;spk304@nyu.edu'})
                response = urllib2.urlopen(req)
                search_results = response.read()
                results = json.loads(search_results)
                data = results['items']
                urlList = []
                for record in data:
                        urlList.append(record['link'])
                        
                return urlList

        #Parses url and adds to both Queue and dictinoary. Used for urls returned 
        def parseurl(self,url):
                #print("from Google:"+url)
                urlobj=URL(url)
                the_page = self.getPage(url)
                if os.path.exists('Downloads')==False:
                        os.mkdir('Downloads')
                        logging.info("Downloads directory created")
                if urlobj.fileName not in self.dictionary and the_page != None: 
                        self.dictionary[urlobj.fileName]=urlobj
                        localfile=open('Downloads/'+urlobj.fileName,'w')
                        localfile.write(the_page)
                        score=self.getPagePriority(urlobj.fileName)
                        self.count=self.count+1
                        print("from Google: "+url + " :Score: " + str(score*-1))
                        heapq.heappush(self.urlList,(score,urlobj))
                        self.qDictionary[urlobj.fileName]=urlobj
                        logging.info("Copied: " + url + "  FileName: "+urlobj.fileName+ "Is Crawlable: "+ str(urlobj.isCrawlable))

        #Returns Page of a given URL 
        def getPage(self,url):
                try:
                        req = urllib2.Request(url,None,{ 'User-Agent' : 'sscrawler' , 'From':'skn262@nyu.edu;spk304@nyu.edu'})
                        response = urllib2.urlopen(req)
                        the_page = response.read()
                        return the_page
                except HTTPError as e:
                        print('The server couldn\'t fulfill the request for: '+url+' :Error code: ', e.code)
                        logging.info("The server couldn\'t fulfill the request for: " + url + "Error: "+str(e.code))
                        global eCount
                        eCount = eCount + 1
                        return None
                
                except URLError as e:
                        print ('We failed to reach a server for: '+url+' :Reason: '+str(e.reason))
                        global eCount
                        eCount = eCount + 1
                        logging.info("The server couldn\'t fulfill the request for: " + url + " :Error: "+str(e.reason))
                        return None
                
                except IOError:
                        print 'We failed to open the File for: '+url
                        global eCount
                        eCount = eCount + 1
                        logging.info("The server couldn\'t fulfill the request for: " + url + "Error: Falied to open file")
                        return None
                except ValueError:                   
                        logging.info("The server couldn\'t fulfill the request for: " + url + "Error: Unknown type")
                        global eCount
                        eCount = eCount + 1
                        print 'Unknown Type of URL: '+url
                        return None
                        
                       

        #Returns All the urls in a Given URL
        def getURL(self,urlobj):
                urll=[]
                if(urlobj.isCrawlable):
                        print("Currently Parsing : "+urlobj.rawUrl)
                        parser = URLLister()
                        localfile=open('Downloads/'+urlobj.fileName,'r')
                        parser.feed(localfile.read())
                        parser.close()
                        localfile.close()
                        
                        for url in parser.urls:

                                if url.startswith("//"):
                                        url=url.replace("//", "http://",1)
                                
                                purl=urlparse(url)
                                if  url == '#' or url.startswith("#") or url.startswith("javascript:"):
                                        break
                                
                                if purl.netloc == "":
                                        url=urljoin(urlobj.rawUrl,url)
                                #self.count=self.count+1
                                urll.append(url)
                        return urll
                return None
        

        #Returns the Negative Score has when we pop heapq we get the Least Score value
        def getPagePriority(self,filename):
                html = open('Downloads/'+filename).read()
                soup = BeautifulSoup(html)
                [s.extract() for s in soup(['style','script','[document]', 'head', 'title'])]
                visible_text = soup.getText().encode('utf-8').strip()
                splitstr=self.serachQuery
                count=0
                for searchstr in splitstr.split():
                        n=len(re.findall(searchstr.lower(),visible_text.lower()))
                        if n != 0:
                                count=count+100+n
                return (count*-1)

def main():
        
        n=100
        maxtotalFiles=100
        crawler = Crawler()
        crawler.serachQuery = 'Dell inspiron 14R'
        errorCount=0
        #Get top 10 Urls From Google
        urlListGoogle=crawler.getURLFromGoogle(crawler.serachQuery)

        for url in urlListGoogle:
                crawler.parseurl(url) #Add the URLS to Queue and Dichtnory

        while (len(crawler.urlList)!=0) and (len(crawler.dictionary)!=n):
                if maxtotalFiles < crawler.count:
                        break
                urll=[]

                #Get URL with Highest Score  
                poped=heapq.heappop(crawler.urlList)
                poopedScore= poped[0]
                popedUrl=poped[1]
                
                #Gets all the crawlable Urls
                urll=crawler.getURL(popedUrl)

                if popedUrl.fileName not in crawler.dictionary:
                        print("added to Dict: "+popedUrl.rawUrl + "Current Dict Size "+str(len(crawler.dictionary)+1) + " :Score: "+ str(poopedScore*-1) )
                        crawler.dictionary[popedUrl.fileName]=popedUrl                                
                if urll != None:
                        for url in urll:                # Parse Through all the urls from poped Url and add them to heap
                                urlobj=URL(url)
                                if urlobj.fileName not in crawler.qDictionary:
                                        the_page1 = crawler.getPage(url)
                                        if the_page1!=None:
                                                localfile=open('Downloads/'+urlobj.fileName,'w')
                                                localfile.write(the_page1)
                                                heapq.heappush(crawler.urlList,(crawler.getPagePriority(urlobj.fileName),urlobj))
                                                crawler.qDictionary[urlobj.fileName]=urlobj
                                                score = crawler.getPagePriority(urlobj.fileName)
                                                crawler.count=crawler.count+1
                                                print("added to Queue: "+url+"  Score: "+str(score*-1))
                                                logging.info("Copied: " + url + " :FileName: "+urlobj.fileName+ " :Is Crawlable: "+ str(urlobj.isCrawlable) +" :Score: "+ str(score*-1))

        global eCount                        
        folderSize=sum(os.path.getsize('Downloads/'+f) for f in os.listdir('Downloads') if os.path.isfile('Downloads/'+f))                                       
        logging.info("Total Files Downloaded: " + str(crawler.count) + " :Total  errors: " + str(eCount) + " :Total Files size: "+ str(folderSize))

                

                
if __name__ == '__main__':
        main()
