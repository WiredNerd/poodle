from pprint import pprint

import pluggy

from poodle import Mutant

# add_mutators = [temp]

# only_mutators = ["Subscript"]

hookimpl = pluggy.HookimplMarker("poodle")

@hookimpl(specname="filter_mutations")
def summarize_mutations(mutants: list[Mutant]) -> None:
    print("summarize_mutations")
    count_by_name = {}
    count_by_file = {}
    count_by_file_mut = {}
    for mutant in mutants:
        if mutant.mutator_name not in count_by_name:
            count_by_name[mutant.mutator_name] = 1
        else:
            count_by_name[mutant.mutator_name] += 1

        key = str(mutant.source_file)
        if key not in count_by_file:
            count_by_file[key] = 1
        else:
            count_by_file[key] += 1

        key = (str(mutant.source_file), mutant.mutator_name)
        if key not in count_by_file_mut:
            count_by_file_mut[key] = 1
        else:
            count_by_file_mut[key] += 1

    pprint(count_by_name)
    # pprint(count_by_file)
    # pprint(count_by_file_mut)
