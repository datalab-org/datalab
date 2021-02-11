# datalabvue
* The new and slightly improved data management system
* Someone think of a good name that isn't taken by Google

## Installation:
Before starting, be warned– the javascript app environment installation will take up at least 300 mb.
Choose where you would like to put the direcotry, and `git clone https://github.com/the-grey-group/datalab.git` 

This repository includes two pieces: a python-based flask server, and a javascript-based vue web application. To install, you will need to install environments for each part.

### Server
1. Make sure you have a recent version of python 3 (tested with python 3.8 and above)
2. install pipenv if you don't have it (`pip install pipenv`)
4. install MongoDB community edition if you don't have it (https://docs.mongodb.com/manual/installation/)
	* if on mac, you may want to do this with homebrew
	* I recommend also installing [MongoDB Compass](https://www.mongodb.com/products/compass), or another GUI client
5. Setup mongodb to run as a service on your computer (or run manually each time you use the site)
6. In mongodb, create a Database called "datalabvue" with a collection called "data". You can do this with the mongo shell or in Compass
7. go into `datalabvue/server` directory and install the python dependencies with pipenv:

	`pipenv install`
  
8. Once the pipenv is set up, activate it from the terminal by typing:

  `pipenv shell`

9. Run the server:
  
  `python main.py`
 
Now, the server should be accessible from localhost:5001/ (there isn't much to see there since this server renders no content, just JSON). 
When the source code is changed, the server will generally automatically reload without needing to manually stop and start the server, though sometimes
this will be necessary. 

NOTE: You may have to chage the `MONGO_URI` config in `main.py` depending on your mongodb setup.

### Web app
1. In a separate terminal window, navigate to `datalabvue/webapp`
2. Make sure you have `npm` installed ("https://www.npmjs.com/get-npm") and updated (`npm install npm@latest -g`, or `sudo sudo npm install npm@latest -g` if on mac)
3. Install all the javascript packages needed. WARNING: This will install almost 300 mb of packages!  
`npm install`
4. Run the webapp from a development server:
`npm run serve`

Similar to the flask development server, this will provide a development environment that serves the web app and automatically reloads it as changes are made to the source.
