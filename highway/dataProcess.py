import os


lookdist = 2  # 2
lookcells = []



for i in range(-lookdist, lookdist + 1):
    for j in range(-lookdist, lookdist + 1):
        if (abs(i) + abs(j) <= lookdist) and (i != 0 or j != 0):
            lookcells.append((i, j))
print(lookcells)



# detect the current working directory

# budgets=[1,1.2,1.4,1.6,1.8, 2]
#
#
# for b in budgets:
#
#     path = "D://epresult//random//Q-learning//1w1h//"+str(b)
#     path2 = "D://epresult//random//Sarsa//1w1h//" + str(b)
#     print("Budget:"+ str(b))
#
#     # read the entries
#     count = 0
#     resultSum = 0
#     min=999999
#     distance=0
#
#     with os.scandir(path2) as listOfEntries:
#         for entry in listOfEntries:
#             # print all entries that are files
#             if entry.is_file():
#                 x=entry.name
#                 if "Enclosing" in x:
#                     tmp=x.split("_")
#                     tmpch=tmp[len(tmp)-1].split(".")[0].replace('y','')
#
#                     if int(tmpch)>distance:
#                         distance=int(tmpch)
#                         count += 1
#                         resultSum += distance
#
#     print("Distance:"+str(distance))
#     if count > 0:
#         print("Average Distance:" + str(resultSum/count))
#                     # count +=1
#                     # enclosingTime=x.split("_")
#                     # resultSum += int(enclosingTime)
#                     # if int(enclosingTime)< int(min) :
#                     #     min=enclosingTime
#         # if count>0:
#         #     averageSum = resultSum/count
#         #     print(str(averageSum))
#         #     print(str(min))