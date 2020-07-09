#!/usr/bin/env python
 
# get test result from jenkins job - jenkins http python API
# note: script can be called only after junit test results are loaded into job at end of test
 
import urllib3
import base64
import os
import yaml
import sys
import re

colors = {
    "Purple": '\033[48;5;105m',
    "Magenta": '\033[105m',
    "Blue": '\033[104m',
    "Green": '\033[102m',
    "Yellow": '\033[103m',
    "Orange": '\033[48;5;208m',
    "Red": '\033[101m',
    "Grey": '\033[48;5;243m',
    "Brown": '\033[48;5;138m',
    "BOLD": '\033[1m',
    "END": '\033[0m',
}
job_id = str(sys.argv[1])

# Replace with your Jenkins instance:
# https://ocs4-jenkins.rhev-ci-vms.eng.rdu2.redhat.com/job/qe-deploy-ocs-cluster/  <-- should be replaced
jenkins_instance = 'https://ocs4-jenkins.rhev-ci-vms.eng.rdu2.redhat.com/job/qe-deploy-ocs-cluster'
url_test_report = f"{jenkins_instance}/{job_id}/testReport/api/python"
job_url = f"{jenkins_instance}/{job_id}/api/python"


# Create your own squads.
# Squads are seperated by Python packages in your project so it is importent to put the squad name in '.' --> ".squad_name."
# For example: In case this test fails - tests.e2e.registry.test_pod_from_registry.TestRegistryImage.test_run_pod_local_image
# the squad is ".registry." as can be seen in the Magenta squad below
squads = {
    'Brown': [".nodes."],
    'Green': [".pv_services.", ".storageclass."],
    'Blue': [".monitoring."],
    'Red': [".mcg."],
    'Yellow': [".cluster_expansion."],
    'Purple': [".test_must_gather.", ".upgrade."],
    'Magenta': [".workloads.", ".registry.", ".logging.", ],
    'Grey': [".performance."],
    'Orange': [".scale."],
    
}
analysis_required = {}
skips = {}
username = ""
password = ""
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
http = urllib3.PoolManager()
result = http.request('GET', url_test_report)
data = yaml.full_load(result.data)
oldClassName = ""
suites=data['suites']
for suite in suites:
    for case in suite['cases']:
        if case['className'] != oldClassName:
            oldClassName = case['className']
        skipped = ""
        if case['skipped']:
            skipped = " SKIP(%s)" % case['skippedMessage']
        if case['status'] == 'FAILED' or case['skipped']:
            for squad, res in squads.items():
                for item in res:
                    if item in case['className']:
                        case_class = '.'.join(case['className'].split('.')[2:])
                        if squad not in analysis_required and case['status'] == 'FAILED':
                            analysis_required[squad] = []
                        elif squad not in skips and case['skipped']:
                            skips[squad] = []
                        if case['status'] == 'FAILED':
                            analysis_required[squad].append(f"{case_class}::{case['name']}")
                        else:
                            skips[squad].append(f"{case_class}::{case['name']}:\n       Reason: {case['skippedMessage']}")

print(f"Hi,\n\nPlease analyze:")
if analysis_required:
    print(f"\n{colors['BOLD']}Failures:{colors['END']}")
    print(f"*********")
    for squad, failures in analysis_required.items():
        print(f"\n{colors[squad]}{squad}{colors['END']} squad:")
        for failure in failures:
            print(f"   - {failure}")

if skips:
    print(f"\n{colors['BOLD']}Skips:{colors['END']}")
    print(f"******")
    for squad, skipped in skips.items():
        print(f"\n{colors[squad]}{squad}{colors['END']} squad:")
        for skip in skipped:
            print(f"   - {skip}")
print(f"\nThanks")



