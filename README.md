# AlgoCatan

Developer Names: Jake Read, Rebecca Di Filippo, Sunny Yao, Matthew Cheung

Sept 2025 - Apr 2026 

## About our project
Our project presents a specialized competitive arena designed for benchmarking
autonomous Catan agents against both human players and existing Catan bots.
By extending the open-source Catanatron framework and game engine, we engineered
a high-performance reinforcement learning agent utilizing a combination of
self-play, curriculum learning, and intensive hyperparameter tuning.
These techniques allowed the bot to iteratively refine its strategic
decision-making environment. As a result of our work, our best performing Catan
agent successfully outperformed the world’s premier publicly available playable
bots, advancing the field of Catan bots. We also promote the teaching of Catan
through experiential learning by enabling players to look back over games
against bots and receive LLM-generated explanations for why a bot made a
given move, promoting the understanding and incorporation of strategies in
future play.

This project is built off the open-source Catanatron framework,
which provides a robust environment for developing and testing Catan agents.
We have made significant modifications to the package, including adding new
modules, to support our specific needs.

## Link

Follow this link to see our arena and play against our bots: \
https://rlcatan.vercel.app/

## Organization
The folders and files for this project are as follows:

src - Source code for the project, including the modified Catanatron library, bot implementations, and training scripts \
docs - Documentation for the project \
refs - Reference material used for the project, including papers \
src/tests - Unit tests for the project


## Installation

See INSTALL.md for installation instructions.


## Simulations

For bot vs. bot batch simulations, pass the arguments below (This will run an example sim):
1. `cd src`
2. `venv\Scripts\activate` 
3. `catanatron-play --num 1 --players AB:2:True,AB:2:True --config-vps-to-win 15 --config-discard-limit 9`

Options:

Create a replay link to view a CLI game --step-db
`catanatron-play --num 1 --players AB:1:True,ABPP:1:True --config-vps-to-win 15 --config-discard-limit 9 --step-db`

Here are some example sims for the bots we created 

To test PlacementPlayer vs. AlphaBetaPlayer
`catanatron-play --num 1 --players AB:2,ABPP:2 --config-vps-to-win 15 --config-discard-limit 9`

To test PPOPlayer vs. ValueFunctionPlayer
`catanatron-play --num 100 --players PPOP,F --config-vps-to-win 15 --config-discard-limit 7`

For more information on the arguments, see the Catanatron documentation: \
https://docs.catanatron.com/


## Deep Learning Training

Navigate to training folder under \src\rlcatan\training using
`cd src\rlcatan\training`

Run \
`python3 looped_trainer.py -runs 5 -iter 1000000` \
Iter is the number of training steps, runs is how many times it is trained for those iterations

Benchmarking Different Model Snapshots: \
`catanatron-play --num 100 --players PPOP:ppo_v3,PPOP:ppo_v3_6 --config-vps-to-win 15 --config-discard-limit 7`


## Unit Tests

We use pytest for unit testing. To run all tests, navigate to the src folder and run \
`pytest`

To run a specific test file, use the command below, replacing the path with the path to the desired test file: \
`python -m pytest src/tests/web/test_api_extra.py`


## Design Doc Module Traceability
The design docs for this project can be found in the docs folder.
These docs outline the architecture and design decisions made during the development of the project,
including the modules and components of the system.
The repo is quite large, and is heavily integrated with the Catanatron codebase.
As such, the path to the relevant code for each module is listed below:

- Training Pipeline: A variety of scripts found under `src\rlcatan\training`. Different scripts were used in different situations.
- Curriculum Learning Manager: `src\rlcatan\training\curriculum.py` and `curriculum_callback.py`
- Elo League System: `src\rlcatan\training\league.py`. The current league state can be found in `src\rlcatan\training\models\league`
- User Interface: `src\ui`. This folder contains the code for the web interface.
- Explanation Pipeline: `src\catanatron\catanatron\explanation`. This folder contains the code for generating explanations for bot moves. It was added as a new Catanatron module.
- Backend API Server: `src\catanatron\catanatron\web\api.py`. This is a modified version of Catanatron's existing API server, which includes new endpoints for the web interface and explanation pipeline.
- AI Model: Various model files found under `src\rlcatan\training\models`.
- Game State Database: `src\catanatron\catanatron\web\database_accumulator.py`. Game state accumulation was part of the existing Catanatron codebase. We used this feature to enable replays in our web UI.
- Game State Manager: Anything unmentioned above and under `src\catanatron` is part of this module. The game state manager is heavily integrated with the Catanatron codebase, so there is no single file or folder that contains all of the relevant code, although the main control is in `game.py`.
We modified many of the existing Catanatron modules to support our project, but most changes were small and the overall structure of the codebase is still intact. The most significant changes were made to `src\catanatron\catanatron\models\player.py`, to support move explanations.
