# ugandaRemoteSensingScraper
This script scrapes every [Sentinel 2](http://www.esa.int/Our_Activities/Observing_the_Earth/Copernicus/Sentinel-2) image of specific areas in Uganda taken in the the last month. It queries the API using Python's `urllib` asks the user for feedback on which new images to download, and then downloads them using `wget` (because the API is old and plays nicely with it).

To modify the locations, change the `locations` list in `main()`. For more complex edits, replace the url in the query function to whatever you want by following the instructions on [this API's documentation](https://scihub.copernicus.eu/userguide/5APIsAndBatchScripting)

## TODO
- [x] Download multiple images at the same time
- [ ] Make the downloading two at a time actually work the way it is supposed to	
- [ ] Checksums
- [ ] Automatically unzipping the files downloaded
- [ ] Catch more errors from wget 
- [ ] Find out why urllib takes a really long time to authenticate

## Long-Term Goals
- [ ] Make RGB image from downloaded files
- [ ] Crop images to each village under study and export in useable format
- [ ] Make NDVI calculations for each file

## Really Long-Term Goals
- [ ] Identify clouds
  - [ ] Mask clouds
  - [ ] Use masked cloud images to make composite images
- [ ] Identify places where the forest was cut down
  - [ ] Quantify area the amount of deforstation that was done in for each village
- [ ] QGIS integration???
