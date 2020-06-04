# Waseda Syllabus Scraper

[![Build Status](https://travis-ci.com/wasedatime/waseda-syllabus-scraper.svg?branch=master)](https://travis-ci.com/wasedatime/waseda-syllabus-scraper)

This is a web scraper built to scrape course information from the [Syllabus Search Database at Waseda University](https://www.wsl.waseda.jp/syllabus/JAA101.php?pLng=en).

## Getting Started

### Prerequisites

* [Python 3](https://www.python.org/downloads/), version >= 3.6.2.
* pip3 (package manager for Python3)
* [jq](https://stedolan.github.io/jq/download/)
* [MongoDB shell](https://docs.mongodb.com/getting-started/shell/installation/) version >= 3.6.0.
* [Robo 3T](https://robomongo.org/) (Optional but recommended)

### Installing

**NOTE:** Currently, this guide is written for Mac users. The general procedure also applies to Window users, but the input commands might be different.

Installations for Python 3, MongoDB shell, and Robo 3T are pretty straight-forward, so they are not covered.

#### Dev dependencies

After installing Python 3, run the command below inside your terminal/command line to check it's available. Note that it is **python3**, not python.

```
python3 --version
```

Run the next command to check if pip3 is available.

```
pip3 --version
```

For more questions, follow the detailed guide [here](https://packaging.python.org/tutorials/installing-packages/) and replace all python, pip command with **python3** and **pip3**.

Install virtual environment for Python 3 by running

```
pip3 install virtualenv
```

Create a folder that will be used as a virtual environment for this project.

```
mkdir wsl-scraper-venv
```

Initialize and activate the environment.

```
virtualenv wsl-scraper-venv
source wsl-scraper-venv/bin/activate
```

Clone this project into the virtual environment folder, and install dev dependencies.

```
cd wsl-scraper-venv
git clone https://github.com/wasetime/waseda-syllabus-scraper.git
pip3 install -r requirements-dev.txt
```

#### MongoDB shell

Run the following command to check if MongoDB shell is available.

```
mongo --version
```

You should see an output like MongoDB shell version v3.6.0.

Remember that you **must start the database process** before scraping so that the scraped data can be exported to MongoDB.


### Customize your scraper

#### variables

#### Schools

All the schools are listed in [data/academics.json](data/academics.json).
You can specify the schools you want to scrape in [data/academics_to_scrape.json](data/academics_to_scrape.json).


### Start scraping

Type the following command inside your terminal

```
cd server
bash scrape.sh
```

#### For Pycharm Users

Remember to set the environment variable `PYTHONIOENCODING=UTF-8` in PyCharm so that 
the utf-8 characters are displayed properly instead of `u\xxx`

Depending on the target you selected,
the scraping process may take a few minutes.

After finish scraping, you can deactivate the virtual environment by typing the following command

```
deactivate
```

### Data validation

You can use mongo shell (pure CLI) or Robo3T (provides a great GUI) to validate if the interested data is scraped and stored correctly in MongoDB.

### Extract classroom and building collections from courses

The Waseda syllabus database only provides data related to courses. In order to obtain classroom and building information, we have extract and group them into separate collections. This can be done using [MongoDB's Aggregation Framework](https://docs.mongodb.com/manual/aggregation/).

This project contains a `aggregate.js` file that helps automating the entire aggregation process. However, it is necessary to change some variables inside before starting.

### Customize your aggregation

Currently, there is no written guide for this section, but you can follow the comments in `aggregate.js` to tweak and customize your own aggregation process.

### Start aggregating

Type the following command inside your terminal to use mongo shell to load the aggregation script.

```
mongo localhost:27017/syllabus /path/to/aggregate.js
```

It should return `true` if the aggregation is successful.

### Congratulations!

If you have obtained the desired results, congratulations! Or
if you encountered some troubles during scraping or aggregating the data, feel free to submit an issue. :)

## Advanced Topics

### Continuous Integration and Deployment

This project is deployed on a remote server, and uses continuous integration and deployment 
with the help Travis CI. You can learn more about the setup process at  
[continuous_deployment.md](docs/continuous_deployment.md)

Unfortunately, currently there are no unit tests
created to ensure the code quality.

### Automated Scraping

This project is deployed on a remote server, which is set up to scrape,
aggregate, and export the data automatically to a remote database.
You can learn more about the setup process at  
[automated_scraping.md](docs/automated_scraping.md)


## Built With

* [Python3](https://www.python.org/) - The language used.
* [Scrapy](https://scrapy.org/) - The scraping framework used.
* [MongoDB](https://www.mongodb.com/) - The database used for storing results.

## Contributing

Submit an issue or a pull request!

## Author

* **Oscar Wang** - _Initial work_ - [OscarWang114](https://github.com/OscarWang114)
* **Taihei Sato** - _Add a new url_ - [tsato815](https://github.com/tsato815)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
