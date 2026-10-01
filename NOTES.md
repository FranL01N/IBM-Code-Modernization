# What I checked, and what the agent got wrong

## What the agent got wrong
The main bug was in the wear calculation. The code used floor division (//) instead of normal division, so a car that had travelled 14,900 km of a 15,000 km service interval could be calculated as 0% wear instead of about 99.3%.

I also found that missing last_service_km values were not handled safely, and the reporting code could fail or calculate averages incorrectly when that value was missing. Another issue was a reversed miles per kilometre conversion constant, which used 1.609 instead of about 0.621371.

I noticed these problems by reading the calculations and then running the tests against known values rather than only checking whether the program executed without errors.
## What I checked before I accepted its work
I checked that the service interval was still 15,000 km and that the warning threshold was still 80%. I specifically made sure the fix only changed the wear calculation and did not change the 80% rule itself.

I ran the test suite after the changes. The final pytest run passed all four tests, including a regression test for a missing service reading. I also checked known outputs directly: 14,900 km out of a 15,000 km interval produced about 99.33% wear, and the report average was calculated using only valid wear readings.

## What the data actually said
The historical data did not support the obvious assumption that older cars or cars with higher total mileage were the main breakdown risks. The average total mileage was almost identical between the two groups, about 53,302 km versus 53,448 km, and average age was also nearly identical at about 5.89 versus 5.88 years.

The clearer differences were how far a car had travelled since its last service and how intensively it was being used. Cars that later broke down had travelled about 11,678 km since service compared with about 7,261 km for cars that did not, and their average daily mileage was about 159.69 km compared with 131.40 km.

Load factor initially looked different as well, but that result became much weaker after checking anomalous rows, so I did not use it in the final risk score. The final score therefore used service-distance and average daily mileage rather than age or total mileage.
