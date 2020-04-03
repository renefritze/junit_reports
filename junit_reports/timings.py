
import sys
from collections import defaultdict
from junitparser import JUnitXml
import os
from tabulate import tabulate


def read_files(filenames):
    """expect filenames of the form test_results_GIT-REV.xml
    """
    results = {}
    for fn in filenames:
        assert os.path.isfile(fn), fn

        xml = JUnitXml.fromfile(fn)
        class_times = defaultdict(lambda : float(0))
        case_times = defaultdict(lambda : float(0))
        for suite in xml:
            # handle suites
            for case in suite:
                class_times[case.classname] += case.time
                name_wo_fixture = case.name[:case.name.find('[')]
                case_times[f'{case.classname}__{name_wo_fixture}'] += case.time
        results[fn] = {'class_times': class_times, 'case_times': case_times}

    return results


def _process_times(res, category, min_time, top_percentile, common_name):
    assert not (min_time and top_percentile)
    data = res[f'{category}_times'].items()
    total_time = sum((x[1] for x in data))
    data = sorted([(a.replace(common_name or '', ''), b, f'{b/total_time*100:.2f}') for a, b in data if min_time is None or b > min_time],
                  key=lambda x: x[1], reverse=True)

    if top_percentile:
        partial = 0
        stop = total_time * top_percentile / 100
        for idx, (_, t, _) in enumerate(data):
            partial += t
            if stop < partial:
                break
        data = data[:idx+1]
    return tabulate(data, headers=(f'{category} name', 'cumulative (s)', '% total'),
                       floatfmt=(".1f", ".3f"),  tablefmt="github")


def report(results, min_time=None, top_percentile=None, common_name=None):
    for fn, res in results.items():
        print('\n')
        print(_process_times(res, 'class', min_time, top_percentile, common_name))
        print('\n')
        print(_process_times(res, 'case', min_time, top_percentile, common_name))


if __name__ == '__main__':
    percent = 90
    common_name = 'src.pymortests.'
    print(f'Showing tests that build the top {percent} percentile in total runtime')
    report(read_files(sys.argv[1:]), min_time=None, top_percentile=percent, common_name=common_name)