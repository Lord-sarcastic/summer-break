# summer-break
A Django application for recording transactions and generating tax reports

## Technologies used
- Server application:
    - [Django](https://djangoproject.com/), Django is a high-level Python web framework that encourages rapid development and clean, pragmatic design.
    - [PostgreSQL](https://www.postgresql.org/), an open source object-relational database system.
    - [Postman](https://www.getpostman.com/), a complete API development environment, and flexibly integrates with the software development cycle for API testing.
    - [Swagger](https://swagger.io), Simplify API development for users, teams, and enterprises with an open source and professional toolset.
    - [Docker](https://www.docker.com/), Containerization platform to run, build and share applications seamlessly

## Installation
Docker is the preferred option for running this application

### Docker
If you've got Docker installed, simply clone `.env.example` as `.env` file and
- Run `make migrate` to run migrations and create necessary tables
- Then run `make up` to start the application

The application should be running on port `8000` at URL: `localhost:8000`.
### Local installation
Running this service locally requires you to install Python, PostgreSQL and Redis. Install them by following the instructions in the link below:
 - Installation directions:
    - I used Python 3.10 as my Python version. You can get that exact version [here](https://www.python.org/downloads/release/python-3100/)
    - PostgreSQL can be downloaded [here](https://www.postgresql.org/download/)

- Basic installation:
    - Install [Python](https://www.python.org/) and [PostgreSQL](https://www.postgresql.org/) on your host environment (or PC).
    - Install [Pipenv](https://pipenv.pypa.io/en/latest/)  which is used to manage the virtual environment using `pip3 install pipenv`.
    - Enter the directory with `cd `
    - Create a `.env` file using the [.env.example](/.env.example) file as a template. Ensure to fill in appropriate values.
    - Run `pipenv install` to install all necessary dependencies for the server application in a virtual environment.
    - Run `pipenv shell` to activate the virtual environment.
    - Next, you run migrations with `python manage.py migrate`.
    - Run the server with `python manage.py runserver`. It should be running on port 8000.


## API Enpoints documentation
The application is made up of 2 endpoints in total handling creating transactions from an uploaded CSV file and generating reports

Documentation for the application is available on [Postman](https://documenter.getpostman.com/view/23092372/2s93RXqpfR). It is also found in the home, `/` route where it is in OpenAPI format and you can also test it there.

## Testing 🚨
Automated tests have been written and you can run tests on Docker with `make test` or `python manage.py test` if you are not using Docker.

If you insist on testing with Postman:
- Install [Postman](https://www.getpostman.com/) or any preferred REST API Client such as [Insomnia](https://insomnia.rest/), [Rest Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client), etc.
- Get the application up and running by following the instructions in the Installation Guide of this README.

## Discussion
This section contains justifications and improvements that should be made.

### Any additional context on your solution and approach, including any assumptions made
I worked with Django framework since I needed to prototype a solution in as less time as possible. Django gives enough tooling to approach the problem 
while focusing on business logic rather than application setup. Looking back, it wouldn't have made much of a difference if I had used
FastAPI since the API logic had little to do with Django's internals.
I made the following assumptions when working on this project:
- An uploaded valid CSV file would have the .csv extension (more on this later)
- The user did not keep a very large file of transactions
- The CSV file had the exact following columns in order: Date, Type, Amount($), Memo

### If you had additional time to work on this problem, what would you add or refine?
This application is supposed to be completed within two (2) to three (3) hours; and while this solution is extensive, I will discuss features I'd have made if I had to implement this in more time:
- More test cases. There are lots of additional functionality that could be tested including:
    - If the validators being called underneath really did the job they did
    - Right file extension, wrong mime type
- Additional features: I belive tax reports are likely to be generated per a certain time period. I would have implemented the following additional features:
    - Allow reports to be generated over a certain time period and interval
    - Validate CSV files beyond file extension and mime type
    - Provide a view of all transactions uploaded over different time periods and filters like: today, three days, this week, this year, last year, and so on.
    - Allow large file uploads by streaming file as CSV rather than reading it all into memory
    - Allow CSV files with several columns while picking only the columns that matter
- Logs. I would have configured a logger for the project and used it extensively
- I would have refined the file validator to be more elegant. The excessive use of throwing errors without clear context and better error dispatching may
make things harder to test
- I would have cached reports on each generation so it doesn't have to be generated each time the endpoint is called and no new transactions have been added

### What are the shortcomings of your solution?
The solution while it works and is well tested has the following shortcomings:
- It can't handle large file uploads and will reject it despite the use of `csv_reader`. I had little time to check if an iterator over `csv.reader` would
yield a stream or simply put everything in memory.
- Rather than show the user certain rows that failed to upload, the API handles this error silently and won't throw any message to the user if no row
was created from an invalid csv file. This behaviour is captured in the `TransactionAPITestCase.test_transactions_will_not_be_created_from_invalid_csv` test.

#### Structure
The application structure would have been more primitive. The current structure is more domain-driven than anything, following Django's convention as inspiration which works pretty well.
