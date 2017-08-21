# ugandaRemoteSensingScraper
This script scrapes every [Sentinel 2](http://www.esa.int/Our_Activities/Observing_the_Earth/Copernicus/Sentinel-2) image of specific areas in Uganda taken in the the last month. It queries the API using Python's `requests` library and asks the user for feedback on which new images to download, and then downloads them using `wget` (because the API is old and plays nicely with it).

To modify the locations, change the `locations` list in `main()`. For more complex edits, replace the url in the query function to whatever you want by following the instructions on [this API's documentation](https://scihub.copernicus.eu/userguide/5APIsAndBatchScripting)

## Dependencies
Run these commands before running this script to install dependencies.
```
pip install requests
```
