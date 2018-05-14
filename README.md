# HardvardIt
Validate the integrity of your student records using THE BLOCKCHAIN.

### Requirements
* Python 3.6 (you can use a virtualenv using `virtualenv -p python3.6 env && source ./env/bin/activate`)
* POA or POW Ethreum-based environment (Quorum, Rinkeby, Kovan, Ropsten)
* Python dependencies defined in `requirements.txt`. To install them use `pip install -r requirements.txt`

### Setup environment
* Install requirements
* Run migrations: `python manage.py migrate`
* Define the connection settings to your blockchain node at `./harvardit/harvardit/eth_settings.py`. You can use this template:
```
eth_host = 'http://localhost'
eth_port = 22001

default_pass = 'Passw0rd'
default_gas = 4000000

initial_ether_transfer = 0

# Only if initial_ether_transfer > 0
coinbase_address = "*"
coinbase_pass = "Passw0rd"

POA = True # Set to false if the consensus used is PoW
```

### Use app
* To run the app from the root of the repository run `cd harvardit && python manage.py runserver`.
* Go to `http://localhost:8000` to start using the app.
* Create a new *Universities*, *Professors* and *Students*, and start playing with the system.

### Inspect student contract
If you want to inspect the data stored in a Smart Contract you can attach to a node 
`geth attach http://<ip>:<port>` and run:
```
loadScript('./scripts/contractInfo.js')
student = contractFactory.at(<contract_address>)
student.grades.call(0)
student.subjectsCompleted.call()
```
