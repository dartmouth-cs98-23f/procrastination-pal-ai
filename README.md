# procrastination-pal-ai

## Description

This repo houses our backend AI service, which responds to textual queries and makes API calls to edit our database accordingly. Our primary backend repo may be found [here](https://github.com/dartmouth-cs98-23f/ProcrastinationPal_backend/tree/main), and our frontend repo, which has more robust project documentation, may be found [here](https://github.com/dartmouth-cs98-23f/procrastination-pal-frontend).

## Architecture

We use OpenAI’s API with an iteration of GPT-4 that allows for "function calling" and "JSON mode." With function calling, our AI can call functions that modify, fetch, and append tasks to a user’s todo list. With JSON mode, we can ensure that data is formatted as JSON before it is passed into functions.

## Setup

- Before running any of the app's backend, make sure you have the proper `.env` file in `/src`. If you don't have it, look [here](https://docs.google.com/document/d/1BACGUCFouUMbxiDyVAjdzcGknfttDYFi93NYbRW98pc/edit?usp=sharing).
- cd into `/src`
- run `pip3 install -r requirements.txt` or `pip install -r requirements.txt` to install requirements.

## Deployment
- Ensure that the [primary backend server](https://github.com/dartmouth-cs98-23f/ProcrastinationPal_backend/tree/main) is running.
- `cd` into `/src` and run `python app.py` or `python3 app.py` to fire up the service.
- Go to our [frontend repo](https://github.com/dartmouth-cs98-23f/procrastination-pal-frontend) and follow the instructions in its `README.md` to test locally.

## Authors

- Nathaniel Mensah
- Carter Sullivan
- Nick Luikey

## Acknowledgments

