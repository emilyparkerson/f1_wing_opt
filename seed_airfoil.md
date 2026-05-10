- The seed airfoil comes from this YouTube video: https://youtu.be/ltyG8Kusay4?si=lsMSu6inj8WI5CZn
- The points are obtained using WebPlotDigitizer
- Each airfoil section is in its own Excel file with the points from WebPlotDigitizer as well as the points adjusted to be in the proper format for JavaFoil (adjusted so that instead of going from LE to lower surface to TE to Upper Surface it now goes TE to upper surace to LE to lower surface)
- Images of these airfoils are in the Excel files, each image contains the camber, camber location, thickness, and thickness locations
- Another image showing the airfoil rotated to 0 AoA is also included. The angles of attack of each airfoil are written in the Excel sheet above the images (don't look at the images for the AoA, look at the value in the cell above the first image)
- Lastly, there is an Excel final containing all the airfoils put together. It has the airfoil coordinates from WebPlotDigitzer as well as the airfoils adjusted to JavaFoil coordinates so that the LE of the center section of the first element is at the origin
- Note that to put airfoils in JavaFoil they have to be separated by a the coordinate 999.9, so when copying the points over make sure to exclude the 999.9 points

