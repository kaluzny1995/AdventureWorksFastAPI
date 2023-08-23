![AW2017MA app logo](app/assets/aw2017ma_api_logo_blue.png)
# AdventureWorks2017 Management API

The AW2017 Management FastAPI is a solution for the maintenance of AdventureWorks2017 datawarehouse. It enables performing four basic CRUD operations on the datawarehouse entities. This project was developed with [FastAPI](https://fastapi.tiangolo.com/) using [Python 3.9.12](https://www.python.org/downloads/release/python-3912/).

## Setup
### 1. Docker & docker-compose
First what you need to install is [Docker](https://www.docker.com/). Proceed with installation instructions from official Docker site. Then install [docker-compose](https://docs.docker.com/compose/install/) tool for Docker container management.

#### 1.1. MongoDB
Use docker-compose tool install MongoDB. Create following files:

**docker-compose.yml**
```yml
services:
    mongo_db:
        image : mongo
        restart: always
        environment:
        - PUID=1000
        - PGID=1000
        - MONGO_INITDB_ROOT_USERNAME=mongo_admin
        - MONGO_INITDB_ROOT_PASSWORD=mongo_admin
        - MONGO_INITDB_DATABASE=awfapi
        volumes:
        - ./mongodb:/data/db
        - ./mongodb-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro
        ports:
        - 27017:27017
```

**mongodb-init.js**
```js
db.createUser(
        {
            user: "mongo_admin",
            pwd: "mongo_admin",
            roles: [
                {
                    role: "readWrite",
                    db: "awfapi"
                }
            ]
        }
);
```
and run command `docker-compose up`.

#### 1.2. PostgresDB
To install PostgresDB with AdventureWorks2017 datawarehouse first download relevant backup from [MSSQL resources](https://learn.microsoft.com/en-us/sql/samples/adventureworks-install-configure?view=sql-server-ver16&tabs=ssms).
Then type in following commands:

```commandline
docker run -p 1433:1433 -e 'ACCEPT_EULA=Y' -e 'SA_PASSWORD=my_password' --restart always -d chriseaton/adventureworks:latest
docker run -p 5452:5432 -e 'POSTGRES_PASSWORD=my_password' --restart always -d chriseaton/adventureworks:postgres
```

### 2. GitHub repo downloading
Download from the [GitHub repo](https://github.com/kaluzny1995/AdventureWorksFastAPI). Open downloaded project repo via PyCharm or other relevant Python IDE.

### 3. Anaconda Python virtual environment
After setting up Docker components and having repo downloaded install [Anaconda](https://www.anaconda.com/). Then set up Python 3.9.12 environment with command:
`conda create -n condaenv39 python=3.9.12 --file requirements.txt`.

## Running FastAPI server

To launch the FastAPI server:
- activate newly created *condaenv39* Python environment via command: `conda activate condaenv39`
- type in `python run.py` or run from `Configurations` from PyCharm. Navigate to `http://localhost:8080/`.
