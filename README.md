# datalabvue
* The new and slightly improved data management system
* Someone think of a good name that isn't taken by Google

## 15 Mar 21 Update:
In this commit, the file system has been completely re-worked. In order to get the new version to run, you will need to create a new collection in your db called "files" (in addition to the "data" collection).

If you don't have any data you want to keep, just delete all the documents in "data" and start over. Things should run. If you want to save old data, you can try going to `server/`, activating the pipenv (`pipenv shell`) and running `python migrate_files_to_files_ObjectId_v2.py`. 

In order to use remote filesystems, you will have to (connect to the chem VPN and) mount Grey group data backup servers on your computer. Then, go into `resources.py` and change the folders to the folders you are interested in. The remote access is currently very slow, so I recommend you restrict the folders to be as small as possible- i.e. just your personal folder on each given server. 

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

## Alternative installation with Docker

These instructions assume that both Docker and docker-compose are installed (and that the Docker daemon is running).

Dockerfiles for the web app, server and database can be found in the `.docker` directory.
- `docker-compose build` will pull each of the base Docker images (`mongo`, `node` and `python:3.8`) and build the corresponding apps on top of them.
- `docker-compose up` will launch a container for each component, such that the web app can be accessed at `localhost:8080`, the server at `localhost:5001` and the database at `localhost:27017`. The source files for the server and the web app are copied at the build stage, so no hot-reloading will occur by default (so `docker-compose build` will need to be called again).
- `docker-compose stop` will stop all running containers.
