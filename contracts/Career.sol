pragma solidity ^0.4.15;

contract Career {
    address public owner;
    mapping (int8 => int8) public grades;

    mapping (address => bool) public professors;
    bool public subjectsCompleted;
    bool public degreeObtained;
    bytes32 public thesis;

    // Checks if it is the owner of the contract, i.e. a University
    modifier isOwner() {
        require(msg.sender == owner);
        _;
    }

    //Checks if is a valid professor for the student
    modifier isProfessor() {
        require(professors[msg.sender] == true);
        _;
    }
    // Checks if all the subjects have been completed
    modifier hasSubjects() {
        require(subjectsCompleted == true);
        _;
    }
    // SC constructor
    constructor() public {
        owner = msg.sender;
        // We use a mapping, we could add other subjects
        grades[0] = -1;
        grades[1] = -1;
        grades[2] = -1;
        subjectsCompleted = false;
        degreeObtained = false;
    }
    // Checks if subjects have been completed.
    function checkCompletedSubjects () private {
        if((grades[0] >= 5) && (grades[1] >= 5) && (grades[2] >= 5)){
            subjectsCompleted = true;
        } else {
            subjectsCompleted = false;
        }
    }
    // Sets grade for a student
    function setGrade (int8 subject, int8 theGrade) public isProfessor() {
        grades[subject] = theGrade;
        checkCompletedSubjects();
    }
    // Sets a professor for a student.
    function setProfessor (address professorAddress) public isOwner() {
        professors[professorAddress] = true;
    }
    // Register and uploaded thesis in the students SC record
    function registerThesis (bytes32 thesisHash) public isOwner() hasSubjects() {
        thesis = thesisHash;
        degreeObtained = true;
    }

}