import urllib.request, json, getpass, re, os

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
    backURL = (")%22)%20AND%20(beginPosition:[NOW-1MONTH%20TO%20NOW]%20AND%20endPosition:"
              "[NOW-1MONTH%20TO%20NOW]%20)%20AND%20(platformname:Sentinel-2)&$select=entry&$orderbyIngestionDate")
    results = {}
    for l in locations:
        print("Querying for "+l['name']+"...",end="")
        # find each product name and UUID
        queryURL =(frontURL+l['coords']+backURL)
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
    # find which files we already have
    have = [x[0] for x in os.walk('.')]
    # make holder list to keep results
    UUIDs = []

    #look for repeats
    for loc in results:
        #find all new files
        news = []
        for i in results[loc]:
            if not (i[0] in have):
                news.append(i[0])
        # ask them if they want to keep the new files
        print("There are "+str(len(news))+" new files for "+loc+":")
        print("Which files would you like to keep?") 
        print("Enter nothing to download all of them, enter a number to download a specific picture"
              ", or enter any letter to stop selecting pictures")
        done = False
        keep = []
        while (not done):
            #reprint the list of pictures
            for n in range(len(news)):
                print("\t"+str(n+1)+"): "+news[n].split('_')[2])

            select = input("Please select: ")
            if len(news)>0:
                if select =="":
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
                        #else it is a letter
                else:
                    done=True
            #if the length of keep is equal to or larger than the pictures to choose from
            else: 
                done = True
        
        #add list of products to keep to the UUIDs list
        for i in results[loc]:
            if i[0] in keep:
                UUIDs = UUIDs + [i[1]]
        print("Finished selection for "+ loc)
    return UUIDs
    
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
        print("Attempting to authenticate...",end='')
        try:
            opener = auth(creds)
            authenticated= True
        except urllib.error.HTTPError:
            print(("\nThere was an error with your authentication. Please reenter your"
                   " credentials and try again. If nothing is working, hit control+c to"
                   " end the loop"))
            creds = getCreds()
        except urllib.error.URLError:
            print(("\nURL error. The URL is broken somehow. This can happen if your"
                   "internet connection is bad or if the ESA is having a bad day"
                   "and their server is down"))
            #allow users to loop or exit
            if (input("Would you like to try again? Enter anything to exit")!=""):
                return(0)
    
    # make new authenticated opener object the default global opener
    urllib.request.install_opener(opener)
    
    # get list of each image UUID and filename that fulfills the query
    results = query(locations)
    print(repeats(results))

if __name__ == "__main__": main()
# "https://scihub.copernicus.eu/dhus/odata/v1/Products('{UUID}')/$value"
