import urllib.request, json, getpass, re 
import xml.etree.ElementTree as ET

def getCreds():
    """gets username and password used to get into sciHub"""
    print("Please enter in your logon credentials for scihub:")
    username = input("Username: ")
    # hide user input while typing password
    password = getpass.getpass("Password: ")
    print("recieved")
    return (username,password)
def auth(creds):
    """Makes a global opener opject to authenticate all further urlopen calls"""
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
    print("\tAuthentication was succsessful")
    return opener

def query(queryURL):
    # get contents and IDs to download
    query = urllib.request.urlopen(queryURL)
    contents= str(query.read()) # TODO check for empty contents 
    # horrible regex fix because the formatting is horrible
    IDs = re.findall('<id>(.*?)</id>',str(contents),re.DOTALL)[1:]
    print("\tFound "+str(len(IDs))+" images that fit the query in the last month")
    return(IDs)

def main():
    """Finds and downloads all Sentinel 2 images of Budongo forest reserve in the last month"""
    #authenticate and make opener object
    frontURL ="https://scihub.copernicus.eu/dhus/search?q=(footprint:%22Intersects("
    backURL = (")%22)%20AND%20(beginPosition:[NOW-1MONTH%20TO%20NOW]%20AND%20endPosition:"
              "[NOW-1MONTH%20TO%20NOW]%20)%20AND%20(platformname:Sentinel-2)&$select=entry")
    coords = ['31.506657652183858,1.6813586688253537']
    # get username and password
    creds = getCreds()
    # make global opener object
    authenticated = False
    while(not authenticated):
        print("Attempting to authenticate...",end='')
        try:
            opener = auth(creds)
            authenticated= True
        except urllib.error.HTTPError:
            print(("\nThere was an error with your authentication. Please reenter your"
                   " credentials and try again. If nothing is working, hit control+c to"
                   "end the loop"))
            creds = getCreds()
        except urllib.error.URLError:
            print(("\nURL error The url is broken somehow. This can happen if your"
                   "internet connection is bad or if the ESA is having a bad day"
                   "and their server is down"))
            #allow users to loop or exit
            if (input("Would you like to try again? Enter anythign to exit")!=""):
                return(0)

    urllib.request.install_opener(opener)
    # loop for each coordinate
    for c in coords:
        print("Querying for coordinates ("+c+")...",end="")
        IDs = query(frontURL+c+backURL)

main()
# "https://scihub.copernicus.eu/dhus/odata/v1/Products('{UUID}')/$value"
