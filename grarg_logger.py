from graphrag.logger.base import ProgressLogger
from tqdm import tqdm


class TqdmProgressLogger(ProgressLogger):
    def __init__(self, total: int):
        self.total = total
        self.progress_bar = tqdm(total=total, desc="Building Index", unit="workflow")

    def success(self, workflow: str):
        self.progress_bar.set_postfix({"Last Workflow": workflow, "Status": "Success"})
        self.progress_bar.update(1)

    def error(self, workflow: str):
        self.progress_bar.set_postfix({"Last Workflow": workflow, "Status": "Error"})
        self.progress_bar.update(1)

    def info(self, message: str):
        self.progress_bar.set_postfix_str(message)

    def close(self):
        self.progress_bar.close()