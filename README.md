# COSC364 RIPv2 Project
### Aljaž Smrekar & Noah Ilogon
### Date: 18/2/25

Distance Vector:
RoutingTable.add_or_update()  
1: New route - install & start timeout timer  
2: Existing Route - Compare & pick best route  
  - Same path and cost: Refresh timer  
  - same next hop better cost: update cost & timer  
  - same hop metric is inf: Poison route  
3: Only switch to new next hop if metric is lower.  


