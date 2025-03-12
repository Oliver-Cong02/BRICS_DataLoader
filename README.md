# BRICS_DataLoader

```bash
g++ -std=c++17 -Wall -O2 -o avltree AVLTree.cpp 
./avltree

txt file name: bric-rev1-002_cam1_1734551081929245.txt
The timecode to be looked up: 1734551081912307
Threshold: 10000
Nearest Timecode: 1734551081922306, frameidx: 000000000000
line in txt file: frame_1734551081922306_000000000000
```

## Parameters:
- threshold: When the difference between the queried timecode and all the timecodes in the txt file exceeds the threshold, it is considered that 'No Frame Found!'.