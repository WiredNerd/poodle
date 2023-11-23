# Compare to Similar

| Mutator Type | Mutmut | Mutatest | Poodle |
| ------------ | ------ | -------- | ------ |
| Binary Operator | Replace with opposite operator | Replace with Random alternate operator | Replace with opposite operator or up to 6 alternates |
| Unary Operator | Remove binary invert '~' | - | Replace '+' with '-'.  Remove 'not' and binary invert '~'. | 
| Augmented Assign | Replace with opposite operator and '=' | Replace +=, -=, *=, /= with random alternate | Replace with = and up to 6 alternates |
| Comparison | Replace with opposite comparison | Replace with random alternate comparison | Replace with 1-2 alternate comparisons. |
| Keywords | 11 keywords | 9 keywords | TBD |
| Number | Change value | - | TBD |
| If Statement | - | Replace with 'if True' and 'if False' | TBD |
| Call replacement | Replace call to Function, Array, or Dict lookup with None | - | TBD |
| Subscript Slice | Number Mutation | Change between [:x], [x:] and [:] | TBD |
| String & F-String | Add "XX" near beginning and end of string | - | TBD |
| Argument | Change field names | - | TBD |
| Lambda | Change return value | - | TBD |
| Expression | Change last value of expression | - | TBD |
| Decorator | Remove decorator | - | TBD |

Disclaimer: These tools internally work very differently so comparison above is not exact.