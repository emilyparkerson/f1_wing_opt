# f1_wing_opt
AA222 Final Project: F1 Multi-Element Rear Wing Optimization<<<<<<< pymead-setup

# To-do

1. In-board and out-board phase 1 geometry (Anthony -- paste plots into report)
a. Plots for each airfoil geometry (seed with new airfoil overlayed)
b. Plots for scoring function for each
c. Plots for drag coefficient and lift coefficient for each

2. In-board and out-board phase 2 geoemetry (only change config and run with single element)
(Mariah -- work on getting intial conditions for phase 2), (Anthony -- get plots same as phase 1, paste plots in report) 
a. Plots for each airfoil geometry (seed with new airfoil overlayed)
b. Plots for scoring function for each
c. Plots for drag coefficient and lift coefficient for each

3. Get results from Pymead optimization for Phase 1 to validate our results (just give Pymead seed airfoil and compare results)
(Emily)
a. Plot comparison between our optimized airfoil and Pymead's
b. Run multiple trials (maybe 5)
i. compare scores between methods
ii. compare robustness and convergence between methods

4. If time permits (probably not)...interface BO optimizer with phase 3 geometry for inboard and outboard
a. Plots for each airfoil showing seed airfoil with new rotated airfoil overlayed
b. Plots for scoring function for each
c. Plots for drag coefficient and lift coefficient for each

For report: (Emily - reorganize report and assign sections)
add section comparing results from Pymead to our own (put in discussion)
add section comparing our fixed airfoils to common high-lift, low Re airfoils (put in discussion)

# Install pymead
In powershell, run the following:
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

This will activate the environment each time it detects it's there in the folder you're in. 

Open/reopen editor (VS Code) and run the following from .\f1_wing_opt :
python -m uv venv f1env --python 3.12
f1env\Scripts\activate
python -m uv pip install pymead

.gitignore will ensure you have your own local f1env without committing it to the main branch

# Linking MSES
After downloading MSES, we have to ensure it's on the path. Claude says:

Step 2: Add that folder to your PATH
There are two ways to do this — a permanent way (recommended) and a quick test way.
The permanent way (Windows GUI):

Press the Windows key and type environment variables
Click "Edit the system environment variables"
In the dialog that opens, click the "Environment Variables..." button at the bottom
You'll see two sections: "User variables" (top) and "System variables" (bottom). Use User variables — it doesn't require admin rights and only affects your account, which is what you want.
In the User variables list, find the row labeled Path and double-click it
Click "New" and paste the MSES folder path you copied
Click OK on all three dialogs to close them

Important: PATH changes only affect new terminal sessions. After saving, fully quit VS Code (close the whole window, not just the terminal) and reopen it. Otherwise the terminal will still have the old PATH.
Step 3: Verify it worked
Open a fresh terminal in VS Code and run:
mses

f1_wing_opt/
