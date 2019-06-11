from sklearn.utils import check_random_state
from sklearn.utils.fixes import sp_version

import numpy as np
class Constraints:
    def __init__(self, constraints_list,space):
        """
        takes a list of constraints. Creates other lists of constraints so that it can more easily be read by validate_sample
        """
        check_constraints(space,constraints_list)
        self.space = space
        self.single = [None for _ in range(space.n_dims)]
        self.inclusive = [[] for _ in range(space.n_dims)]
        self.exclusive = [[] for _ in range(space.n_dims)]
        self.constraints_list = constraints_list
        for constraint in constraints_list:
            if isinstance(constraint,Single):
               self.single[constraint.dimension] = constraint
            elif isinstance(constraint,Inclusive):
                self.inclusive[constraint.dimension].append(constraint)
            elif isinstance(constraint,Exclusive):
                self.exclusive[constraint.dimension].append(constraint)
    def __eq__(self, other):
        if isinstance(other,Constraints):
            return self.constraints_list == other.constraints_list and self.space == other.space
        else:
            return False
    def rvs(self, space, n_samples, random_state = None):
        """ This function tries to sample valid parameter values.
        This is done by first drawing samples with "Single" constraints
        i.e x0 = 1. Then it checks for validity and draws samples untill enough valid samples
        has been drawn.
        Later som more population rules c
        """
        rng = check_random_state(random_state)
        rows  = []
        
        while len(rows) < n_samples: # We keep sampling until all samples a valid with regard to the constraints
            columns = []
            for i in range(space.n_dims):
                dim = space.dimensions[i]
                if self.single[i]:
                    column = np.full(n_samples, self.single[i].value)
                else:
                    if sp_version < (0, 16):
                        column = (dim.rvs(n_samples=n_samples))
                    else:
                        column = (dim.rvs(n_samples=n_samples, random_state=rng))
                columns.append(column)

            # Transpose
            for i in range(n_samples):
                r = []
                for j in range(space.n_dims):
                    r.append(columns[j][i])
                if self.validate_sample(r):
                    rows.append(r)

        return rows[:n_samples]
    def validate_sample(self,sample):
        """ Validates a sample of of parameter values in regards to the constraints
        Parameters
        ----------
        * `sample`:
            A list of values from each dimension to be checked
        * `constraints`

        """
        for dim in range(len(sample)):
            for constraint in self.exclusive[dim]:
                if not constraint.validate_constraints(sample[dim]):
                    return False
            for constraint in self.inclusive[dim]:
                if not constraint.validate_constraints(sample[dim]):
                    return False
        return True
    def __repr__(self):
        return "Constraints({})".format(self.constraints_list)
class Single:
    def __init__(self, dimension, value, dimension_type):
        if dimension_type == 'categorical':
            if not (type(value) == int or type(value) == str or type(value) == float):
                raise TypeError('Single categorical constraint must be of type int, float or str. Got ' + str(type(value)))
        elif dimension_type == 'integer':
            if not type(value) == int:
                raise TypeError('Single integer constraint must be of type int. Got ' + str(type(value)))
        elif dimension_type == 'real':
            if not type(value) == float:
                raise TypeError('Single real constraint must be of type float. Got ' + str(type(value)))
        else:
            raise TypeError('`dimension_type` must be a string containing "categorical", "integer" or "real". got '+str(dimension_type))
        if not (type(dimension) == int):
            raise TypeError('Constraint dimension must be of type int. Got type ' + str(type(dimension)))
        
        self.value = value
        self.dimension = dimension
        self.dimension_type = dimension_type
        self.validate_constraints = self._validate_constraint
    def _validate_constraint(self, value):
        if value == self.value:
            return True
        else:
            return False
    def __repr__(self):
        return "Single(dimension={}, value={}, dimension_type={})".format(self.dimension, self.value, self.dimension_type)
    def __eq__(self, other):
        if isinstance(other,Single):
            return self.value == other.value and self.dimension == other.dimension and self.dimension_type == other.dimension_type
        else:
            return False
class Bound_Constraint():
    """Base class for Exclusive and Inclusive constraints"""
    def __init__(self, dimension, bounds, dimension_type):
        if not type(bounds) == list:
            raise TypeError('Bounds should be a list. Got ' + str(type(bounds)))
        if len(bounds) == 0:
            raise ValueError('Bounds should be a list of length > 0')
        if not dimension_type == 'categorical':
            if not len(bounds) == 2:
                raise ValueError('Length of bounds must be 2 for non-categorical constraints. Got ' + str(len(bounds)))
        self.bounds = bounds
        self.dimension = dimension
        self.dimension_type = dimension_type
        if not (dimension_type == 'categorical' or dimension_type == 'integer' or dimension_type == 'real'):
            raise TypeError('`dimension_type` must be a string containing "categorical", "integer" or "real". got '+str(dimension_type))
        if not (type(dimension) == int):
            raise TypeError('Constraint dimension must be of type int. Got type ' + str(type(dimension)))

        self.bounds = bounds
        self.dimension = dimension
        self.dimension_type = dimension_type

class Inclusive(Bound_Constraint):
    def __init__(self, dimension, bounds,dimension_type):
        """
        bounds is a list.
        If dimension is integer or real numbers between bounds[0] and bounds[1] are included.
        If dimension is categorical all values found in bounds are inluded.
        """
        self.bounds = bounds
        self.dimension = dimension
        self.dimension_type = dimension_type
        if dimension_type == 'categorical':
            self.validate_constraints = self._validate_constraint_categorical
        else:
            self.validate_constraints = self._validate_constraint_real
    def _validate_constraint_categorical(self, value):
        if value in self.bounds:
            return True
        else:
            return False
    def _validate_constraint_real(self, value):
        if value >= self.bounds[0] and value <= self.bounds[1]:
            return True
        else:
            return False
    def __repr__(self):
        return "Inclusive(dimension={}, bounds={}, space_Type={})".format(self.dimension, self.bounds, self.dimension_type)
    def __eq__(self, other):
        if isinstance(other, Inclusive):
            return all([a == b for a, b in zip(self.bounds, other.bounds)]) and self.dimension == other.dimension and self.dimension_type == other.dimension_type
        else:
            return False

class Exclusive(Bound_Constraint):
    def __init__(self, dimension, bounds, dimension_type):
        super().__init__(dimension, bounds, dimension_type) 
        """
        bounds is a list.
        If dimension is integer or real numbers between bounds[0] and bounds[1] are excluded.
        If dimension is categorical all values found in bounds are excluded.
        """
        
        if dimension_type == 'categorical':
            self.validate_constraints = self._validate_constraint_categorical
        else:
            self.validate_constraints = self._validate_constraint_real
    def _validate_constraint_categorical(self, value):
        if value in self.bounds:
            return False
        else:
            return True
    def _validate_constraint_real(self, value):
        if value >= self.bounds[0] and value <= self.bounds[1]:
            return False
        else:
            return True
    def __repr__(self):
        return "Exclusive(dimension={}, bounds={}, dimension_type={})".format(self.dimension, self.bounds, self.dimension_type)
    def __eq__(self, other):
        if isinstance(other, Exclusive):
            return all([a == b for a, b in zip(self.bounds, other.bounds)]) and self.dimension == other.dimension and self.dimension_type == other.dimension_type
        else:
            return False

class Sum:
    def __init__(self, dimensions, bound, bound_type=max):
        """
        Dimension: example [0,3,5]. Deteermnies what dimensions should be summed
        Bound: The constraint on the sum
        bound_type: "min" or "max" Determines if the sum should be minimum a large as the bound or maximum as large.
        """
        self.dimensions = dimensions
        self.bound = bound
        self.bound_type = bound_type

def check_constraints(space,constraints):
    """ Checks if list of constraints is valid
    """
    from .space import Integer, Categorical, Real
    if not type(constraints) == list:
        raise TypeError('Constraints must be a list. Got ' + str(type(constraints)))
    n_dims = space.n_dims
    for i in range(len(constraints)):
        constraint = constraints[i]
        ind_dim = constraint.dimension # Index of the dimension
        if not ind_dim < n_dims:
            raise IndexError('Dimension index ' + str(ind_dim) + ' out of range for n_dims = ' + str(n_dims))
        space_dim = space.dimensions[constraint.dimension]

        # Check if space dimensions types are the same as constraint dimension types
        if isinstance(space_dim,Real):
            if not constraint.dimension_type == 'real':
                raise TypeError('Constraint for real dimension ' + str(ind_dim) + ' must be of dimension_type real. Got ' + str(constraint.dimension_type))
        elif isinstance(space_dim,Integer):
            if not constraint.dimension_type == 'integer':
                raise TypeError('Constraint for integer dimension ' + str(ind_dim) + ' must be of dimension_type integer. Got ' + str(constraint.dimension_type))
        elif isinstance(space_dim,Categorical):
            if not constraint.dimension_type == 'categorical':
                raise TypeError('Constraint for categorical dimension ' + str(ind_dim) + ' must be of dimension_type categorical. Got ' + str(constraint.dimension_type))
        else:
            raise TypeError('Can not find valid dimension for' + str(space_dim))

        # Check if constraints are insinde the bounds of the space
        if isinstance(constraint,Single):
            pass
        elif isinstance(constraint,Inclusive) or isinstance(constraint,Exclusive):
            pass
        else:
            raise TypeError('Constraints must be of type "Single", "Exlusive" or "Inclusive" ')
 