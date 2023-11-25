# Compare to Similar

| Mutator Type | Mutmut | Mutatest | Poodle |
| ------------ | ------ | -------- | ------ |
| Binary Operator | Replace with opposite operator | Replace with Random alternate operator | Replace with opposite operator or up to 6 alternates |
| Unary Operator | Remove binary invert '~' | - | Replace '+' with '-'.  Remove 'not' and binary invert '~'. | 
| Augmented Assign | Replace with opposite operator and '=' | Replace +=, -=, *=, /= with random alternate | Replace with = and up to 6 alternates |
| Comparison | Replace with opposite comparison | Replace with random alternate comparison | Replace with 1-2 alternate comparisons. |
| Keywords | not, is, in, break, continue, True, False, deepcopy, copy, None, and, or | not, is, in, True, False, None, and, or | not, is, in, break, continue, True, False, None |
| Number | Change value | - | Change value |
| String & F-String | Add "XX" near beginning and end of string | - | Add "XX" near beginning and end of string |
| Subscript Slice | See Number Mutation | Change between [:x], [x:] and [:] | See Number Mutation |
| Call replacement | Replace call to Function, Array, or Dict lookup with None | - | Replace call to Function, Array, or Dict lookup with None |
| | | |
| Argument | Change field names | - | TBD |
| Lambda | Change return value | - | TBD |
| Expression | Change last value of expression | - | TBD |
| Decorator | Remove decorator | - | TBD |

Disclaimer: These tools internally work very differently so comparison above is not exact.