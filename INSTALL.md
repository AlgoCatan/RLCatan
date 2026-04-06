## Prerequisites


- Git
- Python 3.11+
- Docker Desktop / Docker Compose
- Only for non-Docker UI development: Node 24 and npm 11+


## Installation

Clone the repository and navigate to the src folder. Then, follow the instructions below based on your operating system.

Windows CMD

1. `python -m venv venv` 
2. `venv\Scripts\activate`
3. `pip install -e .`
4. `pip install -e .[web,gym,dev]`
5. `docker compose up`
6. `docker exec -it src-server-1 pip install "gymnasium<=0.29.1" numpy pandas fastparquet sb3_contrib google-genai`


macOS CMD

1. `python -m venv venv` 
2. `source venv/bin/activate`
3. `pip install -e .`
4. `pip install -e '.[web,gym,dev]'`
5. `docker-compose up`
6. `docker exec -it src-server-1 pip install "gymnasium<=0.29.1" numpy pandas fastparquet sb3_contrib google-genai`


## Uninstallation

To uninstall the project, follow the instructions below based on your operating system.

1. `venv\Scripts\deactivate`
2. `docker compose down --rmi local`
3. Remove the cloned repository folder