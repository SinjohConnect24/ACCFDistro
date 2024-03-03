# importing os module
import os

# path
path = "/home/User/Desktop/file.txt"

# Split the path
head_tail = os.path.split(path)

# print head and tail
print("Head of '% s:'" % path, head_tail[0])
print("Tail of '% s:'" % path, head_tail[1], "\n")

path = "/home/User/Desktop/"

# Split the path
head_tail = os.path.split(path)

# print head and tail
print("Head of '% s:'" % path, head_tail[0])
print("Tail of '% s:'" % path, head_tail[1], "\n")

path = "file.txt"

# Split the path
head_tail = os.path.split(path)

# print head and tail
print("Head of '% s:'" % path, head_tail[0])
print("Tail of '% s:'" % path, head_tail[1])
