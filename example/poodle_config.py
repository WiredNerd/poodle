print("poodle_config.py")

from pathlib import Path
from poodle.mutate.bin_op import BinaryOperationMutator

def temp(**_):
    print("called")
    return []

# add_mutators = [BinaryOperationMutator, temp]
