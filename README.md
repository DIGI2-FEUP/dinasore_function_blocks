# DINASORE Function Blocks

This repository is dedicated to all Function Blocks that might be used in DINASORE and 4DIAC already with a folder organization suitable to several needs. The main idea is to add new or update Functions Blocks according to new developments.

To sync the function blocks with your DINASORE instances, see [sync](#sync).

## FBs

The "FBs" folder contains the set of previously mentioned function blocks. What follows is a brief description of the contents of each sub-folder.

#### ARITHMETIC

In this folder you will find function blocks that perform relatively simple mathematical calculations.

#### CLUSTERING

This folder contains function blocks that perform clustering methods.

#### DATA_HANDLING

This folder contains function blocks that handle the data that is given to them without changing its value.

#### DATA_TRANSFORMATIONS

In this folder you will find function blocks that perform certain operations on data, changing its value.

#### DB

This folder contains function blocks for access and usage of databases.

#### FILES_AND_PLOTS

This folder contains function blocks that read data from files and plot the respective graphs and other representations.

#### MISCELLANEOUS

In this folder you will find function blocks that do not fit in any of the other categories. 

#### MQTT

In this folder you will find function blocks that make use of the MQTT protocol for communication.

#### OPC-UA

This folder contains function blocks that make use of the OPC-UA protocol for information display/fetch.

##### INFO_WRAPPER

<br>
<div align="center"><img src="https://user-images.githubusercontent.com/47611246/134160017-59b17d7d-5d91-4708-aeb9-8570a8b76b30.png" /></div>
<div align="center">Fig. 1 - INFO_WRAPPER function block </div>
<br>

The INFO_WRAPPER function block is a special FB that does not require a python file to be run by DINASORE. Its OpcUa property reads "METHOD" and as such this unique FB serves the purpose of creating OPC-UA methods.

<br>
<div align="center"><img src="https://user-images.githubusercontent.com/47611246/134160555-3ac2782c-c69b-4b84-91b8-c6b2bea911f4.png" /></div>
<div align="center">Fig. 2 - INFO_WRAPPER wrapping connections </div>
<br>

In order to create such a method, pipelines made up of any number of function blocks should be wrapped by this wrapper by connecting its INIT_O property to the event to be fired by the method. Any other event can be connected to its INIT property.

<br>
<div align="center"><img src="https://user-images.githubusercontent.com/47611246/134161052-eb936303-a42e-4f9c-98da-9e9eb11d1eb8.png" /></div>
<div align="center">Fig. 3 - INFO_WRAPPER properties </div>
<br>
    
You can decide what the inputs are for the method by filling out the FB's INPUT property. It expects a list of values in the format "[FUNCTION_BLOCK_NAME.FUNCTION_BLOCK_TYPE]", seperated by commas. Specifying the outputs to be displayed upon the method's conclusion works similarly, but you should naturally fill out the OUTPUT property instead. Finally, the METHOD_NAME property specifies the name of the method. Should these properties be left blank, DINASORE will gather all possible inputs, all outputs and name the method "INFO_WRAPPER".

**Note:** When you deploy a pipeline that is wrapped by INFO_WRAPPER to DINASORE from 4DIAC, DINASORE checks to see which inputs already have a value assigned to them. Consequently, if you specify the value of an input in 4DIAC, you will not have to specify its value again when calling the method.   

##### METHOD_CALLER

<br>
<div align="center"><img src="https://user-images.githubusercontent.com/47611246/134162073-a55f7d1e-838b-4e69-8fb5-9a983f149e99.png" /></div>
<div align="center">Fig. 3 - INFO_WRAPPER properties </div>
<br>

The METHOD_CALLER function block calls the OPC-UA that is specified in its properties. INPUT_VARS expects a list in the format "[X]" where X is the value for an argument of the method. Each value should be seperated by a comma and the values should be in the same order as their respective method arguments. The INPUT_EVENT property is the value that will be assigned to the event being fired by the method. The METHOD_NAME property naturally represents the name of the OPC-UA method and the SERVER_URL is the address for the OPC-UA server that contains the method to be called.

<br>
<div align="center"><img src="https://user-images.githubusercontent.com/47611246/134162178-88e95d1a-f02e-4c58-b26c-04564f8f8d8a.png" /></div>
<div align="center">Fig. 3 - INFO_WRAPPER properties </div>
<br>

The OUTPUT will be a list in the same format as INPUT_VARS. Its values are the ones from the pipeline that the method has finished calling.

#### OPTIMIZATION

This folder contains function blocks that optimize the inputs given.

#### SENSORS_AND_SIMULATORS

This folder contains function blocks that are either sensors, simulators or tools for either of these types of function blocks.

#### TEST

This folder contains function blocks that are used by DINASORE's unit tests.

#### USE_CASES

This folder further contains more folders, each representing a specific use case (pipeline) for which the function blocks that they contain were used.

## sync

The "sync" folder is a package that allows you to synchronize your "FBs" folder with other local or remote DINASOREs.

If the the DINASORE is running local (and not in a Docker), set the address to `localhost` and the port to `-1`.

Synchronization with remote DINASORES requires an SSH connection with the device running the DINASORE in question. Setup a SSH connection in the device running DINASORE using "openssh-server" for example. In your machine you should be able to SSH into the device like `ssh root@x.x.x.x -p 22`.

If you are using Docker locally, don't forget to map the SSH port (by default 22) to the host. The address to be used in Docker locally should be `localhost`. So you would run `ssh root@localhost -p 22`.

### config.json

In this package you will find a configuration file called "config.json". This file has several mandatory fields that you ought to fill out before running the synchronization.

```
{
    "master-fbs-path": # insert the path to the local folder with your function blocks (likely the FBs folder mentioned above),
    "dinasores": [ # array of dinasores to be synchronized       
        {
            "address": # DINASORE address ,
            "port": # DINASORE port ,
            "usename": # SSH username ,
            "password": # SSH password ,
            "dinasore-path": # path to the DINASORE root folder in the device running the DINASORE in question
        }
    ],
    "strategy": # string with each strategy option seperated by whitespace
                # currently there is only the "wipe" strategy which cleans the DINASOREs' function blocks directory
                # before synchronizing it 
}

# EXAMPLE
{
    "master-fbs-path": ".../4diac-ide/typelibrary/fbs/dinasore_function_blocks/FBs",
    "dinasores": [
        {
            "address": "localhost",
            "port": -1,
            "dinasore-path": ".../dinasore"
        },
        {
            "address": "192.168.1.14",
            "port": 22,
            "username": "pi",
            "password": "raspberry"
            "dinasore-path": ".../dinasore"
        }
    ],
    "strategy": "wipe" # OPTIONAL
}
```

### Synchronizing

In order to run the synchronization, simply execute the `synchronize.py` script.
