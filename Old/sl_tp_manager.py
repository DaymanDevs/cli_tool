import json
import os

class SLTPManager:
    def __init__(self, filename="sl_tp_strategies.json"):
        self.filename = filename
        self.strategies = self.load_strategies()

    def load_strategies(self):
        if os.path.exists(self.filename):
            with open(self.filename, "r") as file:
                return json.load(file)
        return {}

    def save_strategies(self):
        with open(self.filename, "w") as file:
            json.dump(self.strategies, file, indent=4)

    def create_strategy(self, name):
        if name in self.strategies:
            raise ValueError("Strategy already exists.")
        self.strategies[name] = []
        self.save_strategies()

    def delete_strategy(self, name):
        if name in self.strategies:
            del self.strategies[name]
            self.save_strategies()

    def rename_strategy(self, old_name, new_name):
        if new_name in self.strategies:
            raise ValueError("A strategy with the new name already exists.")
        self.strategies[new_name] = self.strategies.pop(old_name)
        self.save_strategies()

    def add_step(self, strategy_name, step_type, pl_position, tokens_to_sell):
        if strategy_name not in self.strategies:
            raise ValueError("Strategy does not exist.")
        self.strategies[strategy_name].append({
            "type": step_type,
            "pl_position": pl_position,
            "tokens_to_sell": tokens_to_sell,
        })
        self.save_strategies()

    def edit_step(self, strategy_name, step_index, step_type, pl_position, tokens_to_sell):
        if strategy_name not in self.strategies:
            raise ValueError("Strategy does not exist.")
        if step_index < 0 or step_index >= len(self.strategies[strategy_name]):
            raise IndexError("Invalid step index.")
        self.strategies[strategy_name][step_index] = {
            "type": step_type,
            "pl_position": pl_position,
            "tokens_to_sell": tokens_to_sell,
        }
        self.save_strategies()

    def delete_step(self, strategy_name, step_index):
        if strategy_name not in self.strategies:
            raise ValueError("Strategy does not exist.")
        if step_index < 0 or step_index >= len(self.strategies[strategy_name]):
            raise IndexError("Invalid step index.")
        del self.strategies[strategy_name][step_index]
        self.save_strategies()

    def list_strategies(self):
        return list(self.strategies.keys())

    def get_strategy(self, name):
        return self.strategies.get(name, [])

# Initialize SLTP Manager
sltp_manager = SLTPManager()
