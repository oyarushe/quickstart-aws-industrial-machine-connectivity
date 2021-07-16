
#!/bin/bash

deploy() {
    lambda_fun=$1
    echo "Deploy ${lambda_fun}"
    deployDir="functions/packages/${lambda_fun}"
    rm -rf ${deployDir}
    mkdir ${deployDir}

    deps="functions/source/${lambda_fun}/.deps"
    rm -rf ${deps}
    mkdir ${deps}

    # add dependencies in requirements.txt to zip file
    pip install -r functions/source/${lambda_fun}/requirements.txt -t ${deps}
    pushd ${deps}
    zip -r9 ${OLDPWD}/${lambda_fun}.zip .
    popd

    # add unify_common folder and lambda code to zip file
    pushd "functions/source/"
    zip -g -r ${OLDPWD}/${lambda_fun}.zip unify_common
    zip -g -j ${OLDPWD}/${lambda_fun}.zip ${lambda_fun}/*.py
    popd

    mv ${lambda_fun}.zip ${deployDir}
}

deploy_stack_cleanup() {
    pushd "functions/source/StackCleanup"
    zip -g -j ${OLDPWD}/functions/packages/StackCleanup/stackcleanupfunction.zip ./lambda_function.py
    popd
}

deploy_ggdeployer() {
    pushd "functions/source/ggdeployer"
    zip -g -j ${OLDPWD}/functions/packages/GGDeployer/ggdeployer.zip ./app.py
    popd
}

deploy_all() {
    deploy "UnifyServiceAccountHandler"
    deploy "UnifySiteWiseIngest"
    deploy "UnifySiteWiseUpdater"
    deploy "UnifySourceIngest"
    deploy_stack_cleanup
    deploy_ggdeployer

# deploy to a testing repo s3://imc-unify-demo/unify-quickstart-aws-imc-integratio
    aws s3 sync . s3://imc-unify-demo/unify-quickstart-aws-imc-integration \
    --exclude "*" --include "functions/packages/*" --include "templates/*" --include "scripts/*"
}

deploy_all

# manual run this command if only sync templates:
# aws s3 sync . s3://imc-unify-demo/unify-quickstart-aws-imc-integration --exclude "*"  --include "templates/*"