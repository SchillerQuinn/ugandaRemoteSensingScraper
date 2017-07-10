import urllib.request, json, getpass, re 
import xml.etree.ElementTree as ET


def auth():
    """
    creaetes an opener object that will be used to get into scihub
    """
    username = str(input("Username: "))
    # hide user input while typing password
    password = getpass.getpass("Password: ")
    # create a password manager and handler
    passwordMngr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    done = False
    while (done):
        try:
            passwordMngr.add_password(None, 'https://scihub.copernicus.eu/dhus/', username, password)
            done = True
        except: #TODO make it only accept authentication errors
            print("There was an error with your authentication. Please reenter your credentials and try again. If nothing is working, hit command+z to end the loop")
            username = str(input("Username: "))
            password = getpass.getpass("Password: ")
        
    aHandler = urllib.request.HTTPBasicAuthHandler(passwordMngr)
    # create object that will be able to open url requests
    opener = urllib.request.build_opener(aHandler)
    return(opener)

queryUrl = '''https://scihub.copernicus.eu/dhus/search?q=(footprint:%22Intersects(31.506657652183858,1.6813586688253537)%22)%20AND%20(beginPosition:[NOW-1MONTH%20TO%20NOW]%20AND%20endPosition:[NOW-1MONTH%20TO%20NOW]%20)%20AND%20(platformname:Sentinel-2)&$select=entry'''

#authenticate and make opener object
opener = auth()
# set up opener
opener.open(queryUrl)
urllib.request.install_opener(opener)

# make query
query = urllib.request.urlopen(queryUrl)
# get contents and IDs to download
contents= str(query.read())
IDs = re.findall('<id>(.*?)</id>',str(contents),re.DOTALL)[1:]
"https://scihub.copernicus.eu/dhus/odata/v1/Products('{UUID}')/$value"
