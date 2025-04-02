import yaml
from .kyc_agents import Agent
import json

class Supervisor:
    def __init__(self, config_path):
        with open(config_path) as f:
            config = yaml.safe_load(f)
        self.goal = config['supervisor']['goal']
        self.agent_defs = config['supervisor']['sub_agents']
        self.agents = [Agent(**agent_def) for agent_def in self.agent_defs]

    def run_all(self, customer_data, callback=None):
        task_log = {}
        total_steps = len(customer_data) * len(self.agents)
        step = 0

        for customer in customer_data:
            task_log[customer['name']] = {}
            for agent in self.agents:
                if callback:
                    callback(step, total_steps, customer['name'], agent.name)
                result = agent.run(customer)
                task_log[customer['name']][agent.name] = result
                step += 1
        return task_log