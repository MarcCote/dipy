import numpy.testing as npt
import sys
from dipy.workflows.base import IntrospectiveArgumentParser

def dummy_flow(positional_str, positional_bool, positional_int,
               positional_float, optional_str='default', optional_bool=False,
               optional_int=0, optional_float=1.0):
    """ Workflow used to test the introspective argument parser.

    Parameters
    ----------
    positional_str : string
        positional string argument
    positional_bool : bool
        positional bool argument
    positional_int : int
        positional int argument
    positional_float : float
        positional float argument
    optional_str : string, optional
        optional string argument (default 'default')
    optional_bool : bool, optional
        optional bool argument (default False)
    optional_int : int, optional
        optional int argument (default 0)
    optional_float : float, optional
        optional float argument (default 1.0)
    """
    return positional_str, positional_bool, positional_int,\
           positional_float, optional_str, optional_bool,\
           optional_int, optional_float


def test_iap():
    sys.argv = [sys.argv[0]]
    pos_keys = ['positional_str', 'positional_bool', 'positional_int',
                'positional_float']

    opt_keys = ['optional_str', 'optional_bool', 'optional_int',
                'optional_float']

    pos_results = ['test', 0, 10, 10.2]
    opt_results = ['opt_test', 1, 20, 20.2]

    inputs = inputs_from_results(opt_results, opt_keys)
    inputs.extend(inputs_from_results(pos_results))

    sys.argv.extend(inputs)
    parser = IntrospectiveArgumentParser()
    parser.add_workflow(dummy_flow)
    args = parser.get_flow_args()
    all_keys = pos_keys + opt_keys
    all_results = pos_results+opt_results

    # Test if types and order are respected
    for k, v in zip(all_keys, all_results):
        print k, v
        npt.assert_equal(args[k], v)

    # Test if **args really fits dummy_flow's arguments
    return_values = dummy_flow(**args)
    npt.assert_array_equal(return_values, all_results)


def inputs_from_results(results, keys=None):
    prefix = '--'
    inputs = []
    for idx, result in enumerate(results):
        if keys is not None:
            inputs.append(prefix+keys[idx])
        inputs.append(str(result))

    return inputs

test_iap()














