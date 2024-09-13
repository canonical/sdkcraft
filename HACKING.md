
# Setup Guide for developers

## Install dependencies
Install necessary python packages:
```
sudo apt-get install -y gpg gpgv libpython3-stdlib python3-pip python3-setuptools python3-wheel python3-venv python3-minimal python3-pkg-resources python3-apt python3-pip-whl
```


`snapcraft` is the tool to build, package and publish `sdkcraft` snap. 
All these processes run in a self-launched LXD container. Install `snapcraft` and `lxd` by snap: 

```
sudo snap install snapcraft --classic
sudo snap install lxd

# Add current user to the lxd group to give yourself permission to access its resources:
sudo usermod -a -G lxd $USER

# Logout and re-open your user session for the new group to become active.

# Initialize LXD:
lxd init --minimal
```


`spread` is the end-to-end testing tool for sdkcraft. Install spread from 
the [fork](https://github.com/dmitry-lyfar/spread)

```
git clone https://github.com/dmitry-lyfar/spread
cd spread
go install ./...

# make sure $GOPATH/bin directory is included in $PATH
# after successful installation, you should see help message by:
spread -h
```


Python virtual environment makes the project easy to troubleshot and maintain. It's not required but recommended.
```
# Create a virtual env in current dir
python -m venv venv --system-site-packages

# Activate virtual env
source venv/bin/active
```
> Note: you have to enable `--system-site-packages` option for python virtual env. 
As some dependencies can only be accessed as system site package, not virtual env package.


Install all python dependency packages:
```
pip install -r requirements-dev.txt
```




## Read the code

Starting on a new project can always be challenging. However, you can begin by looking at this snippet in `snapcraft.yaml` file:
```
apps:
  sdkcraft:
    command: bin/python -m sdkcraft
```
That's where the `sdkcraft` command starts its logic.
By following the `sdkcraft/__main__.py` file, you can gradually trace how the code is executed step by step.


`sdkcraft` is built on top of [craft_parts](https://github.com/canonical/craft-parts).


Using a python virtual environment make it convenient to add logging code in dependency package files. So you can understand the execution logic easier.


## Run tests

```
# Run unit tests
make test-units

# Run integration tests - should run on ubuntu-22.04
make test-integrations

# Run end-to-end tests
make spread
```