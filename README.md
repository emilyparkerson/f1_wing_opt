# f1_wing_opt
AA222 Final Project: F1 Multi-Element Rear Wing Optimization<<<<<<< pymead-setup

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
=======
f1_wing_opt/