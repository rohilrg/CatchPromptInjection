# CatchPromptInjection
This repository is dedicated to addressing the prevalent challenge of prompt injection encountered by Language Model Models (LLMs). By providing insights, strategies, and solutions, we aim to equip developers and practitioners with effective approaches to mitigate and overcome prompt injection issues in the LLM domain. Explore the resources and knowledge shared here to enhance your understanding and effectively tackle prompt injection problems within LLMs. 

## Project in action
To see the project in action here:

![Project in action](docs/CatchPromptInjection.gif)

## Project Report
The project report that gives background and compares different methods to circumvent this problem and explaination of proposed solution is stored here: [Project Report](docs/CatchPromptInjection.pdf)
## Structure
````bash
./CatchPromptInjection/
├── src
│   ├── config
│   │   └── config.json
│   ├── tests
│   │   └── test_detector.py
│   └── detector.py
├── Dockerfile
├── LICENSE
├── Makefile
├── README.md
├── app.py
└── requirement.txt
````
Please remember to the config.json file to control parameters.

## Pre-installation steps:
- Make sure you have python 3+ installed on your computer.
- Make sure you have pip3 package installed on your computer.
- Make sure you clone this package to your computer.

## Install requirements: 
In your terminal/command-line go to the project folder and execute the command below:
```bash
pip install -r requirement.txt
```
## Checking before building
Please run these make commands to make sure the formatting, linting and tests are working.
````commandline
make format
make lint
make test
````

## Local Running 
To run the app locally just run the following command in bash in the root directory of the folder:
````bash
streamlit run app.py
````
Your app is available at: http://localhost:8501

## Running with docker
To run the project with docker simply run the following command to build:
```bash
docker build -t <IMAGE_NAME_TO_GIVE> ./
```
Once the image is built please run the container using this command:
````bash
docker run -p 8501:8501 <IMAGE_NAME_TO_GIVE>
````
Once started the app is available at: http://localhost:8501