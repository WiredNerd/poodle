"""Collection of Mutators."""

from .calls import DecoratorMutator, DictArrayCallMutator, FunctionCallMutator, LambdaReturnMutator, ReturnMutator
from .compare import ComparisonMutator
from .constant import KeywordMutator, NumberMutator, StringMutator
from .operators import AugAssignMutator, BinaryOperationMutator
from .unary_op import UnaryOperationMutator
