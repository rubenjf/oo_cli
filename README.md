# HP Operations Orchestration client

This is a python library and command line tool to interact with HP OO. The motivation is that you can use the command line tool as part of a continuous integration pipeline. Unlike the HP tool it has sensible exit codes.

## Install

I recommend you use a virtual environment. See [here](http://virtualenvwrapper.readthedocs.org/en/latest/install.html) for instructions on virtualenvwrapper. Then `mkvirtualenv oo_client` followed by:

```
pip install git+https://bitbucket.org/automationlogic/oo_client.git
```

Now run `hpoo -h` to see the help for the command line tool.

Only dependencies are the python requests module which pip will install for you. If you want to use the build function you also need a JDK (for the jar command line tool). Look for a java-devel package on your platform.

## Build

Currently this is the least flexible part of the tool, it will build a content pack from an SVN checkout and optionally create release branches and tags. A simple example:

```
svn co svn://localhost/srv/svn/mmb-oo
cd mmb-oo/trunk/test-content/
mkdir target
hpoo -a build -bp ./
```

Example output:
```
INFO:ContentBuilder:Creating content pack test-content-cp-2.0.1-109-SNAPSHOT.jar
INFO:ContentBuilder:Done
```

## Deploy

This allows you to deploy one or more content packs to a central, if you specify multiple content packs OO will deploy them in the correct order for dependencies.

```
hpoo -a deploy -cp ./target/test-content-cp-2.0.1-109-SNAPSHOT.jar -c https://central.local:8443 -u admin -p admin
```

Example output:
```
INFO:OOClient:Got new deployment ID: 169300006
INFO:OOClient:Starting uploads...
INFO:OOClient:Uploaded test-content-cp-2.0.1-109-SNAPSHOT.jar
INFO:OOClient:Deployment started, waiting up to 300s to complete
INFO:OOClient:Deployed test-content-cp-2.0.1-109-SNAPSHOT.jar successfully
```

## Test

This mode will run all the flows matching a certain pattern and exit 0 only if all the flows succeed. Example:

```
hpoo -a integration_test -cp test-content --filter tests/integration_tests/test_ -c https://central.local:8443 -u admin -p admin
```

Example output:
```
INFO:IntegrationTester:Found the following test flows, running sequentially
INFO:IntegrationTester:Library/mmb1/tests/integration_tests/test_mmb-test.xml
INFO:IntegrationTester:Library/mmb1/tests/integration_tests/test_mmb-test_fail.xml
INFO:OOClient:Running flow: Library/mmb1/tests/integration_tests/test_mmb-test.xml
INFO:OOClient:Flow Library/mmb1/tests/integration_tests/test_mmb-test.xml FINISHED: RESOLVED, link https://central.local:8445/oo/#/runtimeWorkspace/runs/167900122
INFO:OOClient:Running flow: Library/mmb1/tests/integration_tests/test_mmb-test_fail.xml
INFO:OOClient:Flow Library/mmb1/tests/integration_tests/test_mmb-test_fail.xml FINISHED: RESOLVED, link https://central.local:8445/oo/#/runtimeWorkspace/runs/167900135
```

Currently the flows run sequentially but we could make them run in parallel.

## Run flow

You can also run a flow by path or uuid:

```
hpoo -a run -f Library/mmb1/tests/integration_tests/test_mmb-test.xml -c https://central.local:8445 -u admin -p admin
```

## Develop

To run the tests:
```
git clone git@bitbucket.org:automationlogic/oo_client.git
python setup.py test
```

Example using the library yourself:
```
import oo_client.hpoo
c = oo_client.hpoo.OOClient("https://localhost:8443", "admin", "pass", ssl=False)
c.get_run_status(167900135)
```
or to make any rest call that doesn't have a helper method:
```
c.rest.get('version')
```
## Config

This mode can get/set configuration item(s) with four options.

Example setting the value of a system-properties with the specified path to 'blah':

```
hpoo -k -a set_config -path sp1 -type system-properties -value blah -c https://central.local:8445 -u admin -p cloud
```
This is to get a system-properties specified in 'sp1':
```
hpoo -k -a get_config -path sp1 -type system-properties -c https://central.local:8445 -u admin -p cloud
```

When no path but type is specified, get_config will return all configuration items with the specified type:
```
hpoo -k -a set_config -type system-properties -value blah -c https://central.local:8445 -u admin -p cloud
```
While neither is specified, it will return all configuration items:
```
hpoo -k -a set_config -path sp1 -type system-properties -value blah -c https://central.local:8445 -u admin -p cloud
```