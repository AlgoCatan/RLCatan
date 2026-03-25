# RLcatan

Developer Names: Rebecca Di Filippo, Sunny Yao, Matthew Cheung, Jake Read

Sept 2025 -Apr 2026 

## About our project
We trained a bot to play Catan using Reinforcement Learning with PPO. We incorporated CUDA distributed training, optuna hyperparamter tuning, cirriculm learning, self play leauges and reward shaping to improve our bots 
understanding of Catan. 

## Link

Follow this link to see our bot deployed https://rlcatan.vercel.app/

## Organization
The folders and files for this project are as follows:

docs - Documentation for the project
refs - Reference material used for the project, including papers
src - Source code
test - Test cases
etc.


## Installation

Windows CMD

1. `cd src`
2. `python -m venv venv` 
3. `venv\Scripts\activate`
4. `pip install -e .`
5. `pip install -e .[web,gym,dev]`
6. `docker compose up`
7. `docker exec -it src-server-1 pip install "gymnasium<=0.29.1" numpy pandas fastparquet sb3_contrib google-genai`


macOS CMD

1. `cd src`
2. `python -m venv venv` 
3. `source venv/bin/activate`
4. `pip install -e .`
4. `pip install -e '.[web,gym,dev]'`
5. `docker-compose up`
6. `docker exec -it src-server-1 pip install "gymnasium<=0.29.1" numpy pandas fastparquet sb3_contrib google-genai`


## Simulations

For 1v1 rules simulations, pass the arguments below
1. `cd src`
2. `venv\Scripts\activate` 
3. `catanatron-play --num 1 --players AB:2:True,AB:2:True --config-vps-to-win 15 --config-discard-limit 9`

Options 

Create a replay link to view a CLI game --step-db
`catanatron-play --num 1 --players AB:1:True,ABPP:1:True --config-vps-to-win 15 --config-discard-limit 9 --step-db`

To test Placement Player
`catanatron-play --num 1 --players AB:1:True,PP --config-vps-to-win 15 --config-discard-limit 9`

To test placement on alphabetaPlayer
`catanatron-play --num 1 --players AB:1:True,ABPP:1:True --config-vps-to-win 15 --config-discard-limit 9`

To test PPObot
`catanatron-play --num 100 --players PPOP,F --config-vps-to-win 15 --config-discard-limit 7`


## Deep Learning Training
Navigate to training folder under \src\rlcatan\training using
`cd src\rlcatan\training`

Run
`python3 looped_trainer.py -runs 5 -iter 1000000`
Iter is the number of training steps, runs is how many times it is trained for those iterations

Benchmarking
`catanatron-play --num 100 --players PPOP:ppo_v3,PPOP:ppo_v3_6 --config-vps-to-win 15 --config-discard-limit 7`

Unit tests example

`python -m pytest src/tests/web/test_api_extra.py`
