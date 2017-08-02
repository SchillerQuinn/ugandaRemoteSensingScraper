import getpass, re, os, subprocess, sys, readchar, threading, time, requests, hashlib

class sentinel2Downloader:
    def __init__(self, loc):
        #set locations
        self.locations = loc
        self._creds = []
        self._results = {}
        self._downloadList = []
    
    def pull(self):
        """Finds and downloads all Sentinel 2 images of each chosen coordinate in the last month"""

        # get username and password
        self._getCreds()
        self._results = self._query()
        #if there are no new results
        if len(self._results)==0:
            return 1
        # pick which images to download
        self._select()
        # flatten results into a list of downloads
        self._makeQueue()
        self._down()

    def _getCreds(self):
        """gets username and password used to get into sciHub and sets the class variables"""
        print("Please enter in your logon credentials for scihub:")
        username = input("Username: ")
        # hide user input while typing password
        password = getpass.getpass("Password: ")
        self._creds = (username,password)

    def _query(self):
        """Find all UUIDs and product names for all images of each area in the last month"""
        # get contents and IDs to download
        baseURL ="https://scihub.copernicus.eu/dhus/search?q=(footprint:%22Intersects({})%22)%20AND%20(beginPosition:[NOW-1MONTH%20TO%20NOW]%20AND%20endPosition:[NOW-1MONTH%20TO%20NOW]%20)%20AND%20(platformname:Sentinel-2)&$select=entry&$orderbyIngestionDate"
        queryResults = {}
        for l in self.locations:
            print('\n\n')
            print("Querying for "+l['name']+"...")
            # find each product name and UUID
            queryURL = baseURL.format(l['coords'])
            validQuery = False
            while not validQuery:
                try:
                    query = requests.get(queryURL, auth=(self._creds[0],self._creds[1]), timeout= 5)
                    if query.status_code == 200:
                        validQuery=True
                    else:
                        print(query.status_code)
                        if query.status_code == 401:
                            print("Password and username is incorrect. Please renter your login credentials")
                            self._getCreds()
                except requests.exceptions.Timeout:
                    print("The request timed out. Press space to try again or anything else to exit")
                    if readchar.readkey() != " ":
                        # if they don't hit space, return an empty list
                        return []
            contents = query.text
            # horrible regex fix because the formatting is horrible
            titles = re.findall('<title>(.*?)</title>',str(contents),re.DOTALL)[1:]
            IDs = re.findall('<id>(.*?)</id>',str(contents),re.DOTALL)[1:]
            # save filename/UUID pairs in a dictionary
            queryResults[l['name']] = tuple(zip(titles, IDs))
            
        #provide user feedback
        print("\tFound "+str(len(IDs))+" images of "+l['name']+" in the last month")
        return(queryResults)

    def _select(self):
        """find which files we already have"""
    
        #find list of files in current directory
        have = ([str(f).split('.')[0] for f in os.listdir('.') if os.path.isfile(f)])
        # make holder list to keep results
        selected = []

        #look for repeats
        for loc in self._results:
            #find all new files
            news = []
            re = []
            keep = []
            for i in self._results[loc]:
                if (i[0]+"partial" in have):
                    re.append(i[0])
                elif not (i[0] in have):
                    news.append(i[0])
            # ask them if they want to keep the new files
            print("There are "+str(len(news))+" new files for "+loc+".")
            print("There are "+str(len(re))+" incomplete downloads for "+loc+".") 
        
            # give the option to resume all downloads if there are any incomplete ones
            if len(re)>0:
                print("Press space to resume all downloads or hit any other key to skip and start new downloads.")
                if readchar.readkey() == ' ':
                    keep = re
            if len(news)== 0: #if there are no new files
                print("You have already started a download for every image in "+loc)
                return []
            elif len(news)==1: #there is only one new file
                print("There is one new file: "+news[0].split('_')[2])
                print("Would you like to download it? Press space to download it or hit any other key to cancel the download")
                if readchar.readkey() == ' ':
                    keep = keep + news
            else:
                print("Which files would you like to keep?") 
                print("Hit space to space to download all of them, enter a number to download a specific picture. Hit escape twice when you are done selecting.")
                done = False
                keep = []
                while (not done):
                    #reprint the list of pictures
                    for n in range(len(news)):
                        print("\t"+str(n+1)+"): "+news[n].split('_')[2])

                    print("Please select: ",end = "")
                    select = readchar.readkey()
                    print(select)
                    if len(news)>0:
                        if select ==" ":
                            #if they input nothing select everything
                            #add the rest to the list to keep
                                keep = keep + news
                                done = True
                        elif select.isdigit():
                            #make sure they pick a valid number
                            if (select > 0) and (select <= len(news)):
                                #remove the selection from news and add it to keep
                                keep.append(news.pop(select-1))
                                # show what files are left
                                #selected a bad number
                            else:
                                print("That is an invalid number")
                        elif select == "\x1b\x1b": #if they hit escape twice
                            done= True
                        else:
                            print("Invalid input. Hit space to space to download all pictures. Enter a number to download a specific picture. Hit escape twice when you are done selecting.")
                        #if the length of keep is equal to or larger than the pictures to choose from
                    else: 
                        done = True
            print("Finished selection for "+ loc)
            # remove products not in keep list
            for i in self._results[loc]:
                if i[0] not in keep:
                     self._results[loc].remove(i)        
        return selected

    def _makeQueue(self):
        """Flatten results to just a list"""
        queue = []
        for loc in self._results:
            for pic in self._results[loc]:
                queue = queue + [[pic[0],pic[1]]]
        self._downloadList = queue

    def _check(self, filename, UUID):
        """make sure the file downloaded correctly"""
        #calculate md5 hash of downloaded file
        md5Hash = hashlib.md5()
        with open(filename, "rb") as f:
            # do it by chunks to avoid killing memory
            for chunk in iter(lambda: f.read(4096), b""):
                md5Hash.update(chunk)
        md5Hash = md5Hash.hexdigest()
        print(md5Hash) #TODO test
        #find what the md5file should be
        baseURL = "https://scihub.copernicus.eu/dhus/odata/v1/Products('{}')/Checksum/Value/$value"
        query = requests.get(baseURL.format(UUID), auth=(self._creds[0],self._creds[1]), timeout= 5)
        officialHash = query.text
        print(officialHash) #TODO test
        if md5Hash == officialHash:
            print("MD5 checksum succeeded. File was downloaded successfully")
            return True
        else: 
            print("MD5 checksum failed. This means your file didn't download correctly. Would you like to remove the file? You can try to download it again by running this script again. Press 'd' to remove the file or any other key to keep the file and continue.")
            if readchar.readkey() == "d":
                os.remove(filename)
                return False
            return True     

    def _subDown(self,formatting,UUID):
        """use wget to download an image"""
        UUID = formatting[-1]
        filename = formatting[-2]
        command = "wget --no-check-certificate --auth-no-challenge --continue -q --show-progress --user={} --password={} -O {} --progress=bar:noscroll '{}'"
        try:
            download = subprocess.Popen(command.format(*formatting), shell=True)
            pid = download.pid
            download.wait()
        except KeyboardInterrupt:
            print("Download canceled.")
            subprocess.Popen("pkill -9 -P {}".format(pid), shell=True)
            return True
        #notify user that it is done
        if download.returncode == 0:
            print("Finished downloading " + formatting[2][:-7] + "... Performing checksum.")
            return(self._check(formatting[2],UUID))
        if download.returncode ==-2:
            subprocess.Popen("pkill -9 -P {}".format(pid), shell=True)
            print("Download of " + formatting[2][:-7] + " was canceled. Press Enter 'd' to delete the file or just hit Enter to move on")
            if input() == "d":
                os.remove(filename)             
                return False
            return True

    def _down(self):
        """start threads to downloas images"""
        #don't try to download anything if it doesn't exist
        downloadQueue = self._downloadList
        if len(self._downloadList) == 0:
            print("No images to download. Exiting.")
            return(0)
        #tell user they can skip downloads
        print("\n"+"*"*99)
        print("**** Hold down control+c to cancel active downloads. Progress will continue the next time the script is ran ****")
        print("*"*99,end='')
        while len(downloadQueue)>0:
            try:
                if threading.active_count()<3: #main thread + 2 subthreads
                        info = downloadQueue.pop()
                        print("\n\nStarting download for " + info[0])
                        filename = "./{}partial.zip"
                        baseURL = "https://scihub.copernicus.eu/dhus/odata/v1/Products('\\\''{}'\\\'')/$value"
                        UUID = info[1]
                        formatting = [self._creds[0] ,self._creds[1], filename.format(info[0]), baseURL.format(UUID)]
                        t = threading.Thread(target = self._subDown, args=(formatting,UUID, ))
                        t.start()
            except KeyboardInterrupt:
                #force kill wget
                subprocess.Popen("pkill -9 wget", shell=True)
                print("\nCanceling all active download... Press enter to continue to the next downloads or hit control+c again to exit the script.")
                wait = input()
    
def main():
    locations = [dict(name = 'Budongo Forest Reserve',
                      coords='31.506657652183858,1.6813586688253537')] 
    a = sentinel2Downloader(locations)
    a.pull()

if __name__ == "__main__": main()
