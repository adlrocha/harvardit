# HardvardIt

### Requirements
* Python 3.6
* Ethreum-based environment
* Python dependencies defined in `requirements.txt`. To install them use `pip install -r requirements.txt`

### Setup environment
* Install requirements
* Run migrations: `python manage.py migrate`

### Use app

### Inspect student contract
If you want to inspect the data stored in a Smart Contract you can attach to a node 
`geth attach http://<ip>:<port>` and run:
```
loadScript('./scripts/contractInfo.js')
student = contractFactory.at(<contract_address>)
student.grades.call(0)
student.subjectsCompleted.call()
```