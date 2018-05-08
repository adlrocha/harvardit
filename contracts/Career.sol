pragma solidity ^0.4.15;

contract Career {
    address public owner;
    mapping (int8 => int8) public grades;

    mapping (address => bool) public professors;
    bool public subjectsCompleted;
    bool public degreeObtained;
    bytes32 thesis;

    // Check if owner
    modifier isOwner() {
        require(msg.sender == owner);
        _;
    }

    //Check if professor
    modifier isProfessor() {
        require(professors[msg.sender] == true);
        _;
    }

    modifier hasSubjects() {
        require(subjectsCompleted == true);
        _;
    }


    constructor() public {
        owner = msg.sender;
        // We use a mapping, we could add other subjects
        grades[0] = -1;
        grades[1] = -1;
        grades[2] = -1;
        subjectsCompleted = false;
        degreeObtained = false;
    }

    function checkCompletedSubjects () private {
        if((grades[0] >= 5) && (grades[1] >= 5) && (grades[2] >= 5)){
            subjectsCompleted = true;
        } else {
            subjectsCompleted = false;
        }
    }

    function setGrade (int8 subject, int8 theGrade) public isProfessor() {
        grades[subject] = theGrade;
        checkCompletedSubjects();
    }
    
    function setProfessor (address professorAddress) public isOwner() {
        professors[professorAddress] = true;
    }

    function registerThesis (bytes32 thesisHash) public isOwner() hasSubjects() {
        thesis = thesisHash;
        degreeObtained = true;
    }

}