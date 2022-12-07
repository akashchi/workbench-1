@Library(['workbench_lib@PR-38', 'mainlib@0.6.5']) _

properties([
    buildDiscarder(logRotator(daysToKeepStr: "10")),
    parameters([
        string(
            trim: true,
            defaultValue: 'automation/Jenkins/precommit_test_config.yml',
            description: 'Path to E2E test config file relative to repo root',
            name: 'test_config'),
    ])
])

workbenchPreCommit()
