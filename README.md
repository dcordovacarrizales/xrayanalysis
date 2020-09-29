# xrayanalysis
STANDARD OPERATING PROCEDURE
To use this software, you will need to know to use your terminal and git. Some notes on git will be provided in this manual. 

Installing Software:
1. Access your terminal. Before proceeding, make sure that git and Python are installed on your computer. 
    a. You can check if you have git by going to the terminal and typing this command: git --version
2. Clone the project repository 
    a. go to the github repo and copy the project link to clone it 
    b. in your computer terminal, nagivate to the folder where you want the software installed
    c. run "git clone (put the link here)" in the terminal 
3. Before running the software, pull the newest version of the remote repo to your local system. 
    a. Type "git pull" into terminal to update 

Running Software: 
Creating a virtual environment 
1. Make sure you are in the software folder
2. Terminal commands 
    a. Python3 -m venv project_venv
    b. source project_venv/bin/activate
    c. pip install -r (requirements_mac.txt or requirements.txt)
        I. choose one of these files depending on whether you have a Mac or Windows OS
    d. python3 main.py
4. A browser window should open up now. Log into Google with your Harvard email
5. Now follow the prompts on in the terminal to plot the desired XRD data file 


Note: If you would like to make changes to the software, please create a new branch with a detailed branch name and notes, commit, push to the repo, and then intitiate a pull request.

SECURITY NOTE: If you push to the repo, please make sure that you do NOT upload token.pickle. This file contains your log in information to Google. 