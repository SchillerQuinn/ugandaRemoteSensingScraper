import urllib.request, json, getpass, re, os, subprocess, sys, readchar

def getCreds():
    """gets username and password used to get into sciHub"""
    print("Please enter in your logon credentials for scihub:")
    username = input("Username: ")
    # hide user input while typing password
    password = getpass.getpass("Password: ")
    return (username,password)

def auth(creds):
    """Makes a global opener object to authenticate all further urlopen calls"""
    queryURL = "https://scihub.copernicus.eu/dhus/search?q=(platformname:Sentinel-2)&limit=1"
    #queryURL = "https://scihub.copernicus.eu/dhus/odata/v1/Products(%2216902fd3-f323-4014-a950-853ac602e22f%22)/Nodes(%22S1A_IW_SLC__1SDV_20141101T165548_20141101T165616_003091_0038AA_558F.SAFE%22)/Nodes(%22manifest.safe%22)/$value"
    username = creds[0]
    password = creds[1]
    # create a password manager
    passwordMngr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    # try to authenticate and get the data.
    passwordMngr.add_password(None, 'https://scihub.copernicus.eu/dhus/', username, password)
    # create and return object that will be able to open url requests
    aHandler = urllib.request.HTTPBasicAuthHandler(passwordMngr)
    opener = urllib.request.build_opener(aHandler)
    #test opener (this will raise an error if it doesn't work)
    opener.open(queryURL)
    print("\tAuthentication was successful")
    return opener

def query(locations):
    """Find all UUIDs and product names for all images of each area in the last month"""
    # get contents and IDs to download
    frontURL ="https://scihub.copernicus.eu/dhus/search?q=(footprint:%22Intersects("
    backURL = ")%22)%20AND%20(beginPosition:[NOW-1MONTH%20TO%20NOW]%20AND%20endPosition:[NOW-1MONTH%20TO%20NOW]%20)%20AND%20(platformname:Sentinel-2)&$select=entry&$orderbyIngestionDate"
    results = {}
    for l in locations:
        print('\n\n')
        print("Querying for "+l['name']+"...",end="")
        # find each product name and UUID
        queryURL = (frontURL+l['coords']+backURL)
        # add it to the location information
        query = urllib.request.urlopen(queryURL)
        contents= str(query.read()) # TODO check for empty contents 
        # horrible regex fix because the formatting is horrible
        titles = re.findall('<title>(.*?)</title>',str(contents),re.DOTALL)[1:]
        IDs = re.findall('<id>(.*?)</id>',str(contents),re.DOTALL)[1:]
        # save filename/UUID pairs in a dictionary
        results[l['name']] = tuple(zip(titles, IDs))
        
        #provide user feedback
        print("\tFound "+str(len(IDs))+" images of "+l['name']+" in the last month")
   
    return(results)

def repeats(results):
    """find which files we already have"""
    have = [x[0] for x in os.walk('.')]
    # make holder list to keep results
    UUIDs = []

    #look for repeats
    for loc in results:
        #find all new files
        news = []
        re = []
        keep = []
        for i in results[loc]:
            if not (i[0] in have):
                news.append(i[0])
            if (i+"partial" in have):
                 re.append(i[0])
        # ask them if they want to keep the new files
        print("There are "+str(len(news))+" new files for "+loc+".")
        print("There are "+str(len(re))+" incomplete downloads for "+loc+".") 
        
        # give the option to resume all downloads
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
            print("Hit space to space to download all of them, enter a number to download a specific picture. Hit escape when you are done selecting.")
            done = False
            keep = []
            while (not done):
                #reprint the list of pictures
                for n in range(len(news)):
                    print("\t"+str(n+1)+"): "+news[n].split('_')[2])

                print("Please select: ",end = "")
                select = readchar.readkey()
                print(select, end = "")
                if len(news)>0:
                    if select ==" ":
                        #if they input nothing select everything
                        #add the rest to the list to keep
                        keep = keep + news
                        done = True
                    elif select.isdigit():
                        #get rid of floats
                        select = int(select)
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
        #add list of products to keep to the UUIDs list
        for i in results[loc]:
            if i[0] in keep:
                UUIDs = UUIDs + [[i[0],i[1]]]
        return UUIDs

def down(results, creds):
    """use wget to get images"""
    #don't try to download anything if it doesn't exist
    if len(results) == 0:
        print("No images to download. Exiting.")
        return(0)

    baseURL = "https://scihub.copernicus.eu/dhus/odata/v1/Products('\\\''{}'\\\'')/$value"
    
    #tell user they can skip downloads
    print("\n"+"*"*99)
    print("**** Hit control+c to cancel downloads. Progress will continue the next time the script is ran ****")
    print("*"*99,end='')

    #prevent index errors for odd number downloads by downloading the first one first
    
    try:
        if len(results)%2: 
            #set the range. Note, this will cause the next loop to not run if there is only one picture 
            ran = range(1, len(results),2)
            #download the first image first 
            print("\n\nStarting download for " + results[0][0])
            command = "wget --no-check-certificate --auth-no-challenge --continue -q --show-progress --user={} --password={} -O ./{}.zip --progress=bar:noscroll '{}' "
            command = command.format(creds[0] ,creds[1], results[0][0]+"partial",baseURL.format(results[0][1]))
            download = subprocess.Popen(command, shell=True)
            download.wait() 
            if download.poll()== 4:
                #force kill wget
                subprocess.Popen("pkill -9 wget", shell=True)
                raise Exception("Something broke")
        else:
            ran = range(0, len(results),2)
    except KeyboardInterrupt:
        #force kill wget
        subprocess.Popen("pkill -9 wget", shell=True)
        print("\nCanceling download... Press enter to continue to the next downloads or hit control+c again to exit the script.")
        wait = input()
    #download two at a time     
    for i in ran:
        try:
            firstUUID = results[i][1]
            firstProduct  = results[i][0]
            secondUUID = results[i+1][1]
            secondProduct = results[i+1][0]
            print("\n\nStarting downloads for " + firstProduct[:27]+ "... and " + secondProduct[:27]+"...")

            #make commands
            emptyCommand = "wget --no-check-certificate --auth-no-challenge --continue -q --show-progress --user={} --password={} -O ./{}.zip --progress=bar:noscroll '{}' "
           
            # username, password, file save name, where to download the file from
            command1 = emptyCommand.format(creds[0], creds[1],firstProduct+"partial" , baseURL.format(firstUUID))
            command2 = emptyCommand.format(creds[0], creds[1], secondProduct+"partial", baseURL.format(secondUUID))
            
            #start the downloads
            download1 = subprocess.Popen(command1, shell=True)
            download2 = subprocess.Popen(command2, shell=True)

            #wait for them both to finish
            download1.wait()
            download2.wait()
            
            # look for errors
            if download1.poll()== 4 or download2.poll()==4:
                #force kill wget
                subprocess.Popen("pkill -9 wget", shell=True)
                raise Exception("Something broke")
        except KeyboardInterrupt:
            #force kill wget
            subprocess.Popen("pkill -9 wget", shell=True)
            print("\nCanceling downloads... Press enter to continue to the next downloads or hit control+z again to exit the script.")
            wait = input()


def main():
    """Finds and downloads all Sentinel 2 images of each chosen coordinate in the last month"""
    #authenticate and make opener object
    locations = [dict(name = 'Budongo Forest Reserve',
                      coords='31.506657652183858,1.6813586688253537')]  
    
    # get username and password
    creds = getCreds()

    # make global opener object
    authenticated = False
    #TODO find what takes so long around here
    while(not authenticated):
        print("\n\nAttempting to authenticate...",end='')
        try:
            opener = auth(creds)
            authenticated= True
        except urllib.error.HTTPError:
            print("\nThere was an error with your authentication. Please reenter your credentials and try again. If nothing is working, hit control+c to end the loop")
            creds = getCreds()
        except urllib.error.URLError:
            print(("\nURL error. The URL is broken somehow. This can happen if your internet connection is bad or if the ESA is having a bad day and their server is down"))
            #allow users to loop or exit
            if (input("Would you like to try again? Enter anything to exit")!=""):
                return(0)
    
    # make new authenticated opener object the default global opener
    urllib.request.install_opener(opener)
    
    # get list of each image UUID and filename that fulfills the query
    results = query(locations)
    UUIDs =repeats(results)
    down(UUIDs, creds)

    

if __name__ == "__main__": main()
