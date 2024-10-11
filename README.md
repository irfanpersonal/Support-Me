# Support Me

Support Me is a web application designed to empower content creators by offering a platform for users to support them through tiered subscription models. Creators can offer multiple subscription levels, each with different perks and pricing, while users can subscribe and support their favorite creators. The platform allows seamless integration of user roles, subscription management, and secure payments via Stripe.

## Technologies Used

- [Python](https://www.python.org/): A versatile, high-level programming language known for its readability, ease of use, and wide range of applications, including web development, data analysis, artificial intelligence, and more.
- [FastAPI](https://flask.palletsprojects.com/): A modern, high-performance web framework for building APIs with Python, designed for speed and ease of use, leveraging type hints for automatic validation and documentation.
- [SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/): A powerful SQL toolkit and Object-Relational Mapping (ORM) library for Python, enabling developers to interact with databases using Python objects while providing a flexible and efficient query language.
- [Alembic](https://flask-migrate.readthedocs.io/en/latest/): A lightweight database migration tool for use with SQLAlchemy, allowing developers to manage changes to the database schema over time through version-controlled migrations.
- [Stripe] (https://stripe.com/): A leading online payment processing platform that provides tools for accepting and managing payments for businesses, offering a wide range of APIs for seamless integration.
- [Pydantic](https://docs.pydantic.dev/): A data validation and parsing library that ensures type safety and validation for Python data structures.
- [Uvicorn ASGI](https://www.uvicorn.org/): A lightning-fast ASGI server for Python web applications, particularly optimized for frameworks like FastAPI and Starlette, providing asynchronous capabilities for high-concurrency performance.
- [MySQL](https://www.mysql.com/): A widely used open-source relational database management system known for its reliability and performance.

## Setup Instructions

1st - Download the project

2nd - Create a virtual environment using the built in "venv" module.

python3 -m venv .venv

- python3 is the Python Interpreter you want to use
- -m is a flag that says I would like to run a module as a script
- venv is the built in module used to creating virtual environments
- .venv is the virtual environment name I would like to have (convention)

3rd - Install all the dependencies

pip install -r requirements.txt

4th - Now create a .env file in the root of your entire project with the following

To distinguish from development/production mode

FASTAPI_ENV = production or development

The link to your database for Alembic, and it has to be Syncronous

DATABASE_URL_SYNC_VERSION

The link to your database for SQLAlchemy, and it has to be Asyncronous

DATABASE_URL_ASYNC_VERSION

To remove the __pycache__ folders (optional)

PYTHONDONTWRITEBYTECODE = 1

The secret used to unlock the value of the JWT

JWT_SECRET

The amount of time in days until the JWT will expire

JWT_LIFETIME

To be able to send emails

SENDGRID_API_KEY 

SENDGRID_VERIFIED_SENDER

Base URL for Front End, so we can verify account properly

BASE_URL

For Stripe Integration

STRIPE_SECRET_KEY

For Stripe Webhook Integration

STRIPE_WEBHOOK_KEY

5th - Open up your MySQL server and create a database called "SUPPORT_ME". So just copy paste this code in and execute it

CREATE DATABASE SUPPORT_ME;

6th - To create the necessary tables for this application, run the following command

alembic stamp head

7th - Setup the Stripe CLI and once authenticated run this command to forward the Stripe Web Hooks to the already defined route handler

stripe listen --forward-to localhost:4000/api/v1/purchases/webhooks

8th - Run the app.py file to start up the application

DONE